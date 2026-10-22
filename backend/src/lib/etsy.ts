import { config } from "../config.js";
import { prisma } from "../db.js";

const API_BASE = "https://openapi.etsy.com/v3/application";
const TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token";
// Refresh a little before expiry so a request never goes out with a dead token.
const REFRESH_MARGIN_MS = 60_000;

let refreshing: Promise<string> | null = null;

async function refreshAccessToken(refreshToken: string): Promise<string> {
  const res = await fetch(TOKEN_URL, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "refresh_token",
      client_id: config.etsy.clientId,
      refresh_token: refreshToken,
    }),
  });
  if (!res.ok) throw new Error(`Etsy token refresh failed: ${res.status} ${await res.text()}`);
  const body = (await res.json()) as { access_token: string; refresh_token: string; expires_in: number };

  const data = {
    accessToken: body.access_token,
    refreshToken: body.refresh_token,
    expiresAt: new Date(Date.now() + body.expires_in * 1000),
  };
  await prisma.etsyToken.upsert({ where: { id: 1 }, create: { id: 1, ...data }, update: data });
  return data.accessToken;
}

async function getAccessToken(): Promise<string> {
  const stored = await prisma.etsyToken.findUnique({ where: { id: 1 } });
  if (stored && stored.expiresAt.getTime() - Date.now() > REFRESH_MARGIN_MS) return stored.accessToken;

  const refreshToken = stored?.refreshToken ?? config.etsy.initialRefreshToken;
  if (!refreshToken) throw new Error("No Etsy refresh token: set ETSY_REFRESH_TOKEN");

  // Etsy rotates the refresh token on every refresh, so two concurrent
  // refreshes would invalidate each other. Share one in-flight refresh.
  refreshing ??= refreshAccessToken(refreshToken).finally(() => {
    refreshing = null;
  });
  return refreshing;
}

async function etsyFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "x-api-key": config.etsy.apiKey,
      authorization: `Bearer ${await getAccessToken()}`,
      ...(init.body ? { "content-type": "application/json" } : {}),
      ...init.headers,
    },
  });
  if (!res.ok) throw new Error(`Etsy ${init.method ?? "GET"} ${path} failed: ${res.status} ${await res.text()}`);
  return res;
}

export interface EtsyReceipt {
  receipt_id: number;
  buyer_email?: string;
}

// The order.paid webhook only points at the receipt; the buyer's email has to
// be read from the receipt itself (needs the transactions_r scope).
export async function getReceipt(shopId: string, receiptId: string): Promise<EtsyReceipt> {
  const res = await etsyFetch(`/shops/${shopId}/receipts/${receiptId}`);
  return (await res.json()) as EtsyReceipt;
}

// createReceiptShipment. With no tracking_code/carrier_name Etsy just marks the
// receipt as shipped (complete), which is what a digital delivery needs.
// Needs the transactions_w scope.
export async function markReceiptShipped(shopId: string, receiptId: string, noteToBuyer?: string): Promise<void> {
  await etsyFetch(`/shops/${shopId}/receipts/${receiptId}/tracking`, {
    method: "POST",
    body: JSON.stringify({ send_bcc: false, ...(noteToBuyer ? { note_to_buyer: noteToBuyer } : {}) }),
  });
}
