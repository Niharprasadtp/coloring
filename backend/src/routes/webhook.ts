import { randomBytes } from "node:crypto";
import type { FastifyPluginAsync } from "fastify";
import { config } from "../config.js";
import { prisma } from "../db.js";
import { sendUploadEmail } from "../lib/email.js";
import { getReceipt } from "../lib/etsy.js";
import { verifyWebhookSignature } from "../lib/webhookSignature.js";
import { Prisma } from "../generated/prisma/client.js";

interface EtsyWebhookPayload {
  event_type?: string;
  resource_url?: string;
  shop_id?: number | string;
  receipt_id?: number | string;
  buyer_email?: string;
  data?: { receipt_id?: number | string; shop_id?: number | string; buyer_email?: string };
}

// The payload carries a resource_url like
// https://openapi.etsy.com/v3/application/shops/{shop_id}/receipts/{receipt_id};
// explicit id fields are used when present.
function extractIds(p: EtsyWebhookPayload): { shopId: string; receiptId: string } | null {
  const fromUrl = p.resource_url?.match(/\/shops\/(\d+)\/receipts\/(\d+)/);
  const shopId = String(p.shop_id ?? p.data?.shop_id ?? fromUrl?.[1] ?? "");
  const receiptId = String(p.receipt_id ?? p.data?.receipt_id ?? fromUrl?.[2] ?? "");
  return /^\d+$/.test(shopId) && /^\d+$/.test(receiptId) ? { shopId, receiptId } : null;
}

const webhookRoutes: FastifyPluginAsync = async (app) => {
  // The signature covers the exact bytes Etsy sent, so keep the raw body.
  // Scoped to this plugin; other routes keep Fastify's normal JSON parser.
  app.addContentTypeParser("application/json", { parseAs: "buffer" }, (_req, body, done) => done(null, body));

  app.post("/webhooks/etsy", async (req, reply) => {
    const rawBody = req.body as Buffer;
    const valid = verifyWebhookSignature(
      config.etsy.webhookSecret,
      {
        id: req.headers["webhook-id"] as string | undefined,
        timestamp: req.headers["webhook-timestamp"] as string | undefined,
        signature: req.headers["webhook-signature"] as string | undefined,
      },
      rawBody,
    );
    if (!valid) return reply.code(401).send({ error: "invalid signature" });

    let payload: EtsyWebhookPayload;
    try {
      payload = JSON.parse(rawBody.toString("utf8"));
    } catch {
      return reply.code(400).send({ error: "invalid JSON" });
    }

    // Etsy's docs say "order.paid" but live deliveries send "ORDER_PAID".
    const eventType = payload.event_type?.toLowerCase().replace("_", ".");
    if (eventType !== "order.paid") return { ignored: payload.event_type };

    const ids = extractIds(payload);
    if (!ids) {
      req.log.warn({ payload }, "order.paid webhook without shop/receipt ids");
      return reply.code(400).send({ error: "missing receipt id" });
    }
    if (ids.shopId !== config.etsy.shopId) return { ignored: "other shop" };

    // Etsy retries deliveries, so the same receipt can arrive more than once.
    const receiptId = BigInt(ids.receiptId);
    if (await prisma.order.findUnique({ where: { receiptId }, select: { id: true } })) {
      return { duplicate: true };
    }

    // A thrown error here returns 500, which makes Etsy retry later.
    const buyerEmail =
      payload.buyer_email ?? payload.data?.buyer_email ?? (await getReceipt(ids.shopId, ids.receiptId)).buyer_email;
    if (!buyerEmail) {
      req.log.error({ receiptId: ids.receiptId }, "receipt has no buyer email");
      return reply.code(500).send({ error: "buyer email unavailable" });
    }

    const uploadToken = randomBytes(24).toString("base64url");
    try {
      await prisma.order.create({
        data: { receiptId, shopId: BigInt(ids.shopId), buyerEmail, uploadToken },
      });
    } catch (err) {
      // A concurrent retry of the same delivery won the insert.
      if (err instanceof Prisma.PrismaClientKnownRequestError && err.code === "P2002") return { duplicate: true };
      throw err;
    }

    await sendUploadEmail(req.log, buyerEmail, `${config.frontendUrl}/upload/${uploadToken}`);
    return { ok: true };
  });
};

export default webhookRoutes;
