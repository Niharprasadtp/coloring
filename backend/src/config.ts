import { fileURLToPath } from "node:url";

function required(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`Missing required environment variable ${name}`);
  return value;
}

export const config = {
  port: Number(process.env.PORT ?? 8000),
  // Pooled connection string (Neon "-pooler" host or Supabase pooler on port 6543).
  databaseUrl: required("DATABASE_URL"),
  frontendUrl: required("FRONTEND_URL").replace(/\/$/, ""),
  // Public URL of this backend, used to build the PDF download link.
  publicUrl: required("PUBLIC_URL").replace(/\/$/, ""),

  etsy: {
    webhookSecret: required("ETSY_WEBHOOK_SECRET"),
    // Value sent in the x-api-key header: "keystring:shared_secret".
    apiKey: required("ETSY_API_KEY"),
    // App keystring, sent as client_id when refreshing OAuth tokens.
    clientId: required("ETSY_CLIENT_ID"),
    shopId: required("ETSY_SHOP_ID"),
    // Seeds the token table on first use; after that the stored token is used.
    initialRefreshToken: process.env.ETSY_REFRESH_TOKEN,
  },

  // Directory for uploads in progress and finished PDFs. Koyeb's disk is
  // ephemeral, so PDFs disappear on redeploy (see README).
  dataDir: process.env.DATA_DIR ?? "/tmp/cbn-data",
  pythonBin: process.env.PYTHON_BIN ?? "python3",
  processScript: process.env.PROCESS_SCRIPT ?? fileURLToPath(new URL("../scripts/process_image.py", import.meta.url)),
  maxUploadBytes: Number(process.env.MAX_UPLOAD_MB ?? 15) * 1024 * 1024,
  processTimeoutMs: Number(process.env.PROCESS_TIMEOUT_SEC ?? 300) * 1000,
};
