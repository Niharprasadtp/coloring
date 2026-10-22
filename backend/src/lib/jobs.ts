import { spawn } from "node:child_process";
import { readFile, rm, stat } from "node:fs/promises";
import path from "node:path";
import type { FastifyBaseLogger } from "fastify";
import { config } from "../config.js";
import { prisma } from "../db.js";
import { markReceiptShipped } from "./etsy.js";
import { isFormatKey, type FormatKey, type OutputFile } from "./formats.js";

export const uploadsDir = path.join(config.dataDir, "uploads");
export const outputsDir = path.join(config.dataDir, "outputs");

const STDERR_KEEP_BYTES = 4096;
// Progress lines are written to the database at most this often.
const PROGRESS_WRITE_MS = 1000;

// Image processing is the memory hog, so jobs run strictly one at a time.
// Further uploads wait in this chain instead of starting a second Python process.
let queue: Promise<void> = Promise.resolve();
let waiting = 0;

export function queueLength(): number {
  return waiting;
}

export function orderOutputDir(orderId: string): string {
  return path.join(outputsDir, orderId);
}

export function enqueueJob(log: FastifyBaseLogger, orderId: string, inputPath: string, formats: FormatKey[]): void {
  waiting++;
  queue = queue.then(async () => {
    waiting--;
    try {
      await runJob(log.child({ orderId }), orderId, inputPath, formats);
    } catch (err) {
      log.error({ err, orderId }, "job crashed");
    }
  });
}

function runPython(
  inputPath: string,
  outDir: string,
  formats: FormatKey[],
  onProgress: (pct: number, message: string) => void,
): Promise<void> {
  return new Promise((resolve, reject) => {
    const args = [config.processScript, inputPath, outDir, ...formats.flatMap((f) => ["--format", f])];
    const child = spawn(config.pythonBin, args, {
      stdio: ["ignore", "pipe", "pipe"],
      timeout: config.processTimeoutMs,
      killSignal: "SIGKILL",
      env: {
        ...process.env,
        // Stop numpy/OpenCV from starting a thread pool (and arena) per core.
        OMP_NUM_THREADS: "1",
        OPENBLAS_NUM_THREADS: "1",
        MKL_NUM_THREADS: "1",
        OPENCV_NUM_THREADS: "1",
        MALLOC_ARENA_MAX: "2",
        PYTHONUNBUFFERED: "1",
      },
    });

    // stdout carries "PROGRESS <pct> <message>" lines; anything else is ignored.
    let partial = "";
    child.stdout.setEncoding("utf8");
    child.stdout.on("data", (chunk: string) => {
      const lines = (partial + chunk).split("\n");
      partial = lines.pop()!.slice(-1024);
      for (const line of lines) {
        const m = line.match(/^PROGRESS (\d{1,3}) (.*)$/);
        if (m) onProgress(Math.min(100, Number(m[1])), m[2].slice(0, 200));
      }
    });

    // Keep only the tail of stderr so a chatty script can't grow Node's heap.
    let stderr = "";
    child.stderr.setEncoding("utf8");
    child.stderr.on("data", (chunk: string) => {
      stderr = (stderr + chunk).slice(-STDERR_KEEP_BYTES);
    });

    child.on("error", reject);
    child.on("close", (code, signal) => {
      if (code === 0) return resolve();
      const reason = signal === "SIGKILL" ? "killed (timeout or out of memory)" : `exit code ${code}`;
      reject(new Error(`process_image.py ${reason}: ${stderr.trim()}`));
    });
  });
}

// Trust nothing in the manifest: only plain file names that exist in outDir.
async function readManifest(outDir: string): Promise<OutputFile[]> {
  const entries = JSON.parse(await readFile(path.join(outDir, "manifest.json"), "utf8")) as unknown;
  if (!Array.isArray(entries)) throw new Error("manifest.json is not a list");

  const outputs: OutputFile[] = [];
  for (const e of entries) {
    const { file, label, format } = e ?? {};
    if (typeof file !== "string" || file !== path.basename(file) || file === "manifest.json") {
      throw new Error(`manifest.json: bad file name ${JSON.stringify(file)}`);
    }
    if (typeof format !== "string" || !isFormatKey(format)) throw new Error(`manifest.json: bad format ${format}`);
    const info = await stat(path.join(outDir, file));
    outputs.push({ file, label: String(label ?? file), format, size: info.size });
  }
  if (outputs.length === 0) throw new Error("manifest.json lists no files");
  return outputs;
}

async function runJob(log: FastifyBaseLogger, orderId: string, inputPath: string, formats: FormatKey[]): Promise<void> {
  const workDir = path.dirname(inputPath);
  const outDir = orderOutputDir(orderId);

  // Progress writes are chained so they land in order, and throttled.
  let lastWrite = 0;
  let writes: Promise<unknown> = Promise.resolve();
  const onProgress = (progress: number, progressMessage: string) => {
    const now = Date.now();
    if (now - lastWrite < PROGRESS_WRITE_MS && progress < 100) return;
    lastWrite = now;
    writes = writes
      .then(() => prisma.order.update({ where: { id: orderId }, data: { progress, progressMessage } }))
      .catch((err) => log.warn({ err }, "progress update failed"));
  };

  let outputs: OutputFile[];
  try {
    log.info({ formats }, "processing started");
    // Clear files from an earlier failed attempt.
    await rm(outDir, { recursive: true, force: true });
    await runPython(inputPath, outDir, formats, onProgress);
    outputs = await readManifest(outDir);
  } catch (err) {
    log.error({ err }, "processing failed");
    await writes;
    await rm(outDir, { recursive: true, force: true });
    await prisma.order.update({
      where: { id: orderId },
      data: { status: "FAILED", error: "We couldn't process that image. Please try another one." },
    });
    return;
  } finally {
    await rm(workDir, { recursive: true, force: true });
  }

  await writes;
  const order = await prisma.order.update({
    where: { id: orderId },
    data: { status: "COMPLETED", outputs: outputs as object[], progress: 100, progressMessage: "Done", error: null },
  });
  log.info({ files: outputs.length }, "processing finished");

  if (order.etsyShippedAt) return;
  try {
    await markReceiptShipped(order.shopId.toString(), order.receiptId.toString());
    await prisma.order.update({ where: { id: orderId }, data: { etsyShippedAt: new Date(), etsyError: null } });
    log.info("Etsy receipt marked as shipped");
  } catch (err) {
    // The buyer already has their files; record the failure so it can be retried.
    log.error({ err }, "marking Etsy receipt as shipped failed");
    await prisma.order.update({ where: { id: orderId }, data: { etsyError: String(err).slice(0, 1000) } });
  }
}
