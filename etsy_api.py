"""Minimal Etsy Open API v3 client for this shop (stdlib only).

Usage:
    python etsy_api.py login   # one-time: approve access in the browser, saves etsy_token.json
    python etsy_api.py me      # check the connection: prints your user and shop

Reads ETSY_KEYSTRING and ETSY_SHARED_SECRET from .env next to this file.
Tokens are stored in etsy_token.json (gitignored). Access tokens last 1 hour and
are refreshed automatically; the refresh token lasts 90 days.
"""
from __future__ import annotations

import base64
import hashlib
import json
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV_FILE = HERE / ".env"
TOKEN_FILE = HERE / "etsy_token.json"

AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
API_BASE = "https://api.etsy.com/v3/application"

REDIRECT_HOST, REDIRECT_PORT, REDIRECT_PATH = "localhost", 3003, "/oauth/redirect"
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}{REDIRECT_PATH}"
SCOPES = ["listings_r", "listings_w", "listings_d", "shops_r", "shops_w", "transactions_r"]


def load_env() -> dict[str, str]:
    env = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    for key in ("ETSY_KEYSTRING", "ETSY_SHARED_SECRET"):
        if not env.get(key):
            sys.exit(f"Missing {key} in {ENV_FILE}")
    return env


ENV = load_env()
KEYSTRING = ENV["ETSY_KEYSTRING"]
# Etsy's x-api-key header takes "keystring:shared_secret".
API_KEY_HEADER = f"{KEYSTRING}:{ENV['ETSY_SHARED_SECRET']}"


# ---------- OAuth ----------

def _post_form(url: str, data: dict) -> dict:
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST",
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Token request failed ({e.code}): {e.read().decode(errors='replace')}")


def _save_token(tok: dict) -> dict:
    tok["expires_at"] = time.time() + int(tok.get("expires_in", 3600)) - 60
    tok["user_id"] = tok["access_token"].split(".", 1)[0]
    old = json.loads(TOKEN_FILE.read_text()) if TOKEN_FILE.exists() else {}
    if "shop_id" in old:
        tok.setdefault("shop_id", old["shop_id"])
    TOKEN_FILE.write_text(json.dumps(tok, indent=2))
    return tok


def login() -> dict:
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    state = secrets.token_urlsafe(16)
    result: dict[str, str] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urllib.parse.urlparse(self.path)
            if u.path != REDIRECT_PATH:
                self.send_response(404); self.end_headers(); return
            q = dict(urllib.parse.parse_qsl(u.query))
            result.update(q)
            ok = "code" in q and q.get("state") == state
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = ("Connected! You can close this tab and go back to Claude." if ok
                   else f"Something went wrong: {q.get('error_description') or q.get('error') or 'state mismatch'}")
            self.wfile.write(f"<html><body style='font-family:sans-serif;padding:40px'><h2>{msg}</h2></body></html>".encode())

        def log_message(self, *a):
            pass

    params = {
        "response_type": "code",
        "client_id": KEYSTRING,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params, quote_via=urllib.parse.quote)}"

    server = HTTPServer((REDIRECT_HOST, REDIRECT_PORT), Handler)
    server.timeout = 5  # handle_request() returns at least this often
    print("Opening Etsy in your browser. Click 'Allow Access'.")
    print("If it doesn't open, paste this URL into your browser:\n" + url, flush=True)
    webbrowser.open(url)
    deadline = time.time() + 600
    while "code" not in result and "error" not in result and time.time() < deadline:
        server.handle_request()
    server.server_close()

    if result.get("state") != state:
        sys.exit("Login failed: state mismatch or no response.")
    if "code" not in result:
        sys.exit(f"Login failed: {result.get('error_description') or result.get('error')}")

    tok = _post_form(TOKEN_URL, {
        "grant_type": "authorization_code",
        "client_id": KEYSTRING,
        "redirect_uri": REDIRECT_URI,
        "code": result["code"],
        "code_verifier": verifier,
    })
    tok = _save_token(tok)
    print(f"Saved token to {TOKEN_FILE.name}")
    return tok


def get_token() -> dict:
    if not TOKEN_FILE.exists():
        sys.exit("Not logged in. Run: python etsy_api.py login")
    tok = json.loads(TOKEN_FILE.read_text())
    if time.time() >= tok.get("expires_at", 0):
        new = _post_form(TOKEN_URL, {
            "grant_type": "refresh_token",
            "client_id": KEYSTRING,
            "refresh_token": tok["refresh_token"],
        })
        new["shop_id"] = tok.get("shop_id")
        tok = _save_token(new)
    return tok


# ---------- API calls ----------

def _multipart(form: dict, files: dict) -> tuple[bytes, str]:
    """files: {field: Path}. Returns (body, content_type)."""
    boundary = "----etsy" + secrets.token_hex(12)
    parts = []
    for k, v in (form or {}).items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, p in files.items():
        p = Path(p)
        ctype = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".pdf": "application/pdf",
                 ".zip": "application/zip", ".mp4": "video/mp4"}.get(p.suffix.lower(), "application/octet-stream")
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{p.name}"\r\n'
                     f'Content-Type: {ctype}\r\n\r\n'.encode() + p.read_bytes() + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def request(method: str, path: str, params: dict | None = None, json_body: dict | None = None,
            form: dict | None = None, files: dict | None = None, auth: bool = True, retry: bool = True) -> dict:
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    headers = {"x-api-key": API_KEY_HEADER}
    if auth:
        headers["Authorization"] = f"Bearer {get_token()['access_token']}"
    data = None
    if files:
        data, headers["Content-Type"] = _multipart(form, files)
    elif json_body is not None:
        data = json.dumps(json_body).encode(); headers["Content-Type"] = "application/json"
    elif form is not None:
        data = urllib.parse.urlencode(form, doseq=True).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    for attempt in range(4 if retry else 1):
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=600 if files else 60) as r:
                raw = r.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and retry and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode(errors='replace')}") from None
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:   # dropped connection: try again
            if not retry or attempt == 3:
                raise
            print(f"   network error ({e}), retrying {method} {path}", flush=True)
            time.sleep(10 * (attempt + 1))


def me() -> None:
    tok = get_token()
    shop = request("GET", f"/users/{tok['user_id']}/shops")
    if not shop.get("shop_id"):
        print("Connected, but no shop found on this account.")
        return
    tok["shop_id"] = shop["shop_id"]
    TOKEN_FILE.write_text(json.dumps(tok, indent=2))
    print(f"Connected to shop: {shop.get('shop_name')} (shop_id {shop['shop_id']})")
    print(f"Active listings: {shop.get('listing_active_count')}  |  Currency: {shop.get('currency_code')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "me"
    if cmd == "login":
        login()
        me()
    elif cmd == "me":
        me()
    else:
        sys.exit(__doc__)
