import { createReadStream, createWriteStream } from "node:fs";
import { mkdir, rm, stat } from "node:fs/promises";
import path from "node:path";
import { pipeline } from "node:stream/promises";
import type { FastifyPluginAsync, FastifyReply } from "fastify";
import { config } from "../config.js";
import { prisma } from "../db.js";
import { FORMATS, isFormatKey, type FormatKey, type OutputFile } from "../lib/formats.js";
import { enqueueJob, orderOutputDir, queueLength, uploadsDir } from "../lib/jobs.js";

const ALLOWED_TYPES: Record<string, string> = {
  "image/jpeg": ".jpg",
  "image/png": ".png",
  "image/webp": ".webp",
};

const CONTENT_TYPES: Record<string, string> = {
  ".pdf": "application/pdf",
  ".png": "image/png",
  ".swatches": "application/zip",
};

const TOKEN_RE = /^[A-Za-z0-9_-]{20,64}$/;

type TokenParams = { Params: { token: string } };
type FileParams = { Params: { token: string; file: string } };

function httpError(statusCode: number, message: string): Error {
  return Object.assign(new Error(message), { statusCode });
}

function badToken(token: string, reply: FastifyReply): boolean {
  if (TOKEN_RE.test(token)) return false;
  reply.code(404).send({ error: "Upload link not found" });
  return true;
}

const uploadRoutes: FastifyPluginAsync = async (app) => {
  // multipart/form-data with:
  //   formats: one field per selected option (repeatable), keys from FORMATS
  //   image:   the photo
  app.post<TokenParams>("/upload/:token", async (req, reply) => {
    const { token } = req.params;
    if (badToken(token, reply)) return reply;

    // Claim the order atomically so a double submit can't start two jobs.
    const claimed = await prisma.order.updateMany({
      where: { uploadToken: token, status: { in: ["AWAITING_UPLOAD", "FAILED"] } },
      data: { status: "PROCESSING", error: null, progress: 0, progressMessage: "Uploading" },
    });
    if (claimed.count === 0) {
      const order = await prisma.order.findUnique({ where: { uploadToken: token } });
      if (!order) return reply.code(404).send({ error: "Upload link not found" });
      return reply.code(409).send({ error: "This order has already been uploaded", status: order.status });
    }

    const order = await prisma.order.findUniqueOrThrow({ where: { uploadToken: token } });
    const workDir = path.join(uploadsDir, order.id);

    try {
      const formats = new Set<FormatKey>();
      let inputPath: string | null = null;

      for await (const part of req.parts()) {
        if (part.type === "field") {
          if (part.fieldname !== "formats") continue;
          const value = String(part.value);
          if (!isFormatKey(value)) throw httpError(400, `Unknown format "${value}"`);
          formats.add(value);
          continue;
        }

        if (part.fieldname !== "image" || inputPath) {
          part.file.resume();
          throw httpError(400, "Send exactly one file, in the 'image' field");
        }
        const ext = ALLOWED_TYPES[part.mimetype];
        if (!ext) {
          part.file.resume();
          throw httpError(415, "Please upload a JPG, PNG or WebP image");
        }
        // Stream straight to disk: the image is never held in Node's memory.
        await mkdir(workDir, { recursive: true });
        inputPath = path.join(workDir, `input${ext}`);
        await pipeline(part.file, createWriteStream(inputPath));
        if (part.file.truncated) {
          throw httpError(413, `Image is larger than ${config.maxUploadBytes / 1024 / 1024} MB`);
        }
      }

      if (!inputPath) throw httpError(400, "No image uploaded");
      if (formats.size === 0) throw httpError(400, "Choose at least one style or format");

      // Keep the buyer's order of options stable regardless of form order.
      const selected = (Object.keys(FORMATS) as FormatKey[]).filter((k) => formats.has(k));
      const position = queueLength();
      await prisma.order.update({
        where: { id: order.id },
        data: {
          formats: selected,
          progressMessage: position > 0 ? `Waiting for ${position} order(s) ahead of yours` : "Starting",
        },
      });
      enqueueJob(req.log, order.id, inputPath, selected);
      return reply.code(202).send({ status: "PROCESSING", queuePosition: position + 1 });
    } catch (err) {
      // Release the claim so the buyer can try again.
      await rm(workDir, { recursive: true, force: true });
      await prisma.order.update({
        where: { id: order.id },
        data: { status: "AWAITING_UPLOAD", progress: 0, progressMessage: null },
      });
      throw err;
    }
  });

  app.get<TokenParams>("/orders/:token", async (req, reply) => {
    const { token } = req.params;
    if (badToken(token, reply)) return reply;

    const order = await prisma.order.findUnique({
      where: { uploadToken: token },
      select: { status: true, error: true, formats: true, progress: true, progressMessage: true, outputs: true },
    });
    if (!order) return reply.code(404).send({ error: "Upload link not found" });

    const outputs = order.status === "COMPLETED" ? ((order.outputs ?? []) as unknown as OutputFile[]) : [];
    return {
      status: order.status,
      error: order.error,
      formats: order.formats,
      progress: order.progress,
      progressMessage: order.progressMessage,
      files: outputs.map((o) => ({
        label: o.label,
        format: o.format,
        size: o.size,
        name: o.file,
        url: `${config.publicUrl}/download/${token}/${encodeURIComponent(o.file)}`,
      })),
    };
  });

  app.get<FileParams>("/download/:token/:file", async (req, reply) => {
    const { token, file } = req.params;
    if (badToken(token, reply)) return reply;

    const order = await prisma.order.findUnique({ where: { uploadToken: token } });
    const outputs = (order?.outputs ?? []) as unknown as OutputFile[];
    // Only names recorded in the manifest are served, which also rules out path traversal.
    if (!order || order.status !== "COMPLETED" || !outputs.some((o) => o.file === file)) {
      return reply.code(404).send({ error: "File not found" });
    }

    const filePath = path.join(orderOutputDir(order.id), file);
    const info = await stat(filePath).catch(() => null);
    if (!info) return reply.code(410).send({ error: "This file has expired. Please contact the shop." });

    const ext = path.extname(file).toLowerCase();
    return reply
      .header("content-type", CONTENT_TYPES[ext] ?? "application/octet-stream")
      .header("content-length", info.size)
      .header("content-disposition", `attachment; filename="${order.receiptId}-${file}"`)
      .send(createReadStream(filePath));
  });
};

export default uploadRoutes;
