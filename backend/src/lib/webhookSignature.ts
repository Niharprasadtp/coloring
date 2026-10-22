import { createHmac, timingSafeEqual } from "node:crypto";

// Etsy webhooks follow the Standard Webhooks spec (https://www.standardwebhooks.com):
//   webhook-id:        unique message id
//   webhook-timestamp: unix seconds
//   webhook-signature: space-separated "v1,<base64 HMAC-SHA256>" entries
// The signed content is `${id}.${timestamp}.${rawBody}`.

const TOLERANCE_SEC = 5 * 60;

function secretBytes(secret: string): Buffer {
  // Standard Webhooks secrets are "whsec_" + base64 key bytes.
  return secret.startsWith("whsec_") ? Buffer.from(secret.slice(6), "base64") : Buffer.from(secret, "utf8");
}

export function verifyWebhookSignature(
  secret: string,
  headers: { id?: string; timestamp?: string; signature?: string },
  rawBody: Buffer,
  nowSec = Math.floor(Date.now() / 1000),
): boolean {
  const { id, timestamp, signature } = headers;
  if (!id || !timestamp || !signature) return false;

  const ts = Number(timestamp);
  // Reject stale or future-dated messages to block replays.
  if (!Number.isInteger(ts) || Math.abs(nowSec - ts) > TOLERANCE_SEC) return false;

  const expected = createHmac("sha256", secretBytes(secret))
    .update(`${id}.${timestamp}.`)
    .update(rawBody)
    .digest();

  return signature.split(" ").some((entry) => {
    const [version, sig] = entry.split(",", 2);
    if (version !== "v1" || !sig) return false;
    const given = Buffer.from(sig, "base64");
    return given.length === expected.length && timingSafeEqual(given, expected);
  });
}
