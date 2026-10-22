// One-time Etsy OAuth (PKCE) to get the shop owner's refresh token.
//
//   ETSY_CLIENT_ID=<keystring> ETSY_REDIRECT_URI=<registered https URL> node scripts/etsy-oauth.mjs
//
// The redirect URI only has to be registered on the Etsy app; nothing needs to
// be served there. After approving, copy the full URL from the browser's
// address bar (even if the page shows a 404) and paste it here.

import { createHash, randomBytes } from "node:crypto";
import { createInterface } from "node:readline/promises";

const clientId = process.env.ETSY_CLIENT_ID;
const redirectUri = process.env.ETSY_REDIRECT_URI;
if (!clientId || !redirectUri) {
  console.error("Set ETSY_CLIENT_ID and ETSY_REDIRECT_URI");
  process.exit(1);
}

const verifier = randomBytes(32).toString("base64url");
const challenge = createHash("sha256").update(verifier).digest("base64url");
const state = randomBytes(16).toString("hex");

const authUrl = new URL("https://www.etsy.com/oauth/connect");
authUrl.search = new URLSearchParams({
  response_type: "code",
  client_id: clientId,
  redirect_uri: redirectUri,
  scope: "transactions_r transactions_w",
  state,
  code_challenge: challenge,
  code_challenge_method: "S256",
})
  .toString()
  .replace(/\+/g, "%20"); // Etsy's docs encode the scope's space as %20

console.log("\n1. Open this URL while logged in to Etsy as the shop owner, and click Allow:\n");
console.log(authUrl.toString());

const rl = createInterface({ input: process.stdin, output: process.stdout });
const pasted = await rl.question("\n2. Paste the full URL you were redirected to:\n> ");
rl.close();

const params = new URL(pasted.trim()).searchParams;
if (params.get("error")) throw new Error(`Etsy returned ${params.get("error")}: ${params.get("error_description")}`);
if (params.get("state") !== state) throw new Error("state mismatch: paste the URL from this run");

const res = await fetch("https://api.etsy.com/v3/public/oauth/token", {
  method: "POST",
  headers: { "content-type": "application/x-www-form-urlencoded" },
  body: new URLSearchParams({
    grant_type: "authorization_code",
    client_id: clientId,
    redirect_uri: redirectUri,
    code: params.get("code") ?? "",
    code_verifier: verifier,
  }),
});
const body = await res.json();
if (!res.ok) throw new Error(`Token exchange failed: ${res.status} ${JSON.stringify(body)}`);

// The access token is "<user_id>.<token>"; for a shop owner that user id is
// not the shop id, so look the shop up separately (GET /v3/application/users/{id}/shops).
console.log("\nSet this on Koyeb (and in backend/.env):\n");
console.log(`ETSY_REFRESH_TOKEN=${body.refresh_token}`);
console.log(`\nYour Etsy user id: ${body.access_token.split(".")[0]}`);
