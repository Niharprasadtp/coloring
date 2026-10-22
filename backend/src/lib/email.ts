import type { FastifyBaseLogger } from "fastify";

// Mock mailer: logs instead of sending. Swap the body for Resend, Postmark,
// SES, etc. when ready; callers only rely on this signature.
export async function sendUploadEmail(log: FastifyBaseLogger, to: string, uploadUrl: string): Promise<void> {
  log.info({ to, uploadUrl }, "MOCK EMAIL: upload link sent to buyer");
}
