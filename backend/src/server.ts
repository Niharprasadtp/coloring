import cors from "@fastify/cors";
import multipart from "@fastify/multipart";
import Fastify from "fastify";
import { config } from "./config.js";
import { prisma } from "./db.js";
import uploadRoutes from "./routes/upload.js";
import webhookRoutes from "./routes/webhook.js";

const app = Fastify({
  logger: { level: process.env.LOG_LEVEL ?? "info" },
  bodyLimit: 1024 * 1024, // JSON bodies (webhooks) only; uploads use multipart limits below.
  trustProxy: true,
});

await app.register(cors, { origin: config.frontendUrl, methods: ["GET", "POST"] });
await app.register(multipart, {
  limits: { fileSize: config.maxUploadBytes, files: 1, fields: 10, parts: 11 },
});

app.get("/health", async () => ({ ok: true }));
await app.register(webhookRoutes);
await app.register(uploadRoutes);

// Jobs live in memory, so any order still PROCESSING after a restart was cut
// off mid-run. Mark it failed so the buyer can upload again.
const interrupted = await prisma.order.updateMany({
  where: { status: "PROCESSING" },
  data: { status: "FAILED", error: "Processing was interrupted. Please upload your image again." },
});
if (interrupted.count) app.log.warn({ count: interrupted.count }, "reset interrupted orders");

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.once(signal, async () => {
    await app.close();
    await prisma.$disconnect();
    process.exit(0);
  });
}

await app.listen({ host: "0.0.0.0", port: config.port });
