# Etsy fulfillment pipeline

```
Etsy order.paid ──► Fastify /webhooks/etsy (Koyeb) ──► Postgres (Neon/Supabase)
                          │ emails buyer (mock)
                          ▼
buyer ──► Next.js /upload/[token] (Vercel) ──image + formats──► Fastify /upload/:token
                          ▲                                   │ queue (1 at a time)
                          └──── polls /orders/:token ◄────────┤ python3 process_image.py
                                                              │ Etsy createReceiptShipment
                                                              ▼
                                               /download/:token/:file (PDF/PNG/.swatches)
```

| Path | What |
|---|---|
| `Dockerfile` | Backend image for Koyeb (build from repo root) |
| `backend/src/routes/webhook.ts` | `order.paid` webhook: signature check, save order, email link |
| `backend/src/routes/upload.ts` | Upload, status/progress polling, file downloads |
| `backend/src/lib/jobs.ts` | Runs the Python script, records progress, then marks the Etsy receipt shipped |
| `backend/src/lib/formats.ts` | The selectable styles/formats (keys shared with Python and the frontend) |
| `backend/src/lib/etsy.ts` | Etsy API client with OAuth token refresh |
| `backend/scripts/process_image.py` | **Mock** processor: replace with the real color-by-number logic |
| `frontend/app/upload/[token]/page.tsx` | Buyer page: drag-and-drop upload, style checklist, progress, downloads |
| `frontend/app/upload/[token]/formats.ts` | Option labels and descriptions shown to the buyer |

## Backend API

| Route | Purpose |
|---|---|
| `POST /webhooks/etsy` | Etsy webhook target |
| `POST /upload/:token` | multipart: one `formats` field per selected option, plus the `image` file. Returns `202`; processing runs in the background |
| `GET /orders/:token` | `{ status, error, formats, progress, progressMessage, files[] }`, polled by the frontend |
| `GET /download/:token/:file` | One output file (only names listed in the job's manifest) |
| `GET /health` | Koyeb health check |

Statuses: `AWAITING_UPLOAD → PROCESSING → COMPLETED`, or `FAILED` (the buyer can upload again).

Format keys:

| Key | Option |
|---|---|
| `dark` | Dark Numbered Version (PDF + PNG) |
| `light` | Light Numbered Version (PDF + PNG) |
| `palette` | Palette Numbered Version (PDF + PNG) |
| `contour` | Contour/Outline Version, unnumbered (PDF + PNG) |
| `palette_pdf` | Digital + Printable Color Palette (PDF + PNG) |
| `procreate` | Color Palette for Procreate (`.swatches`) |

To add or rename an option, update `backend/src/lib/formats.ts`,
`frontend/app/upload/[token]/formats.ts` and `FORMATS`/`MAKERS` in
`process_image.py` together.

## Setup

### 1. Database (Neon or Supabase)

Create a database and note two connection strings: the **pooled** one
(`DATABASE_URL`, used by the server) and the **direct** one (`DIRECT_URL`,
used only for migrations). Then from `backend/`:

```bash
cp .env.example .env   # fill in DIRECT_URL at least
npm install
npx prisma migrate deploy
```

Run `migrate deploy` the same way whenever the schema changes; the container
does not run migrations at startup.

### 2. Etsy app

1. In the Etsy developer portal, note the app keystring and shared secret.
   `ETSY_API_KEY` is `keystring:sharedsecret`, `ETSY_CLIENT_ID` is the keystring.
2. Register an https callback URL on the app (e.g.
   `https://my-frontend.vercel.app/etsy-callback`; nothing needs to be served
   there), then run the OAuth (PKCE) flow once as the shop owner:
   `ETSY_CLIENT_ID=<keystring> ETSY_REDIRECT_URI=<that URL> node scripts/etsy-oauth.mjs`
   from `backend/`. It prints the `ETSY_REFRESH_TOKEN` to set. After the first refresh the server keeps the
   rotating tokens in the `etsy_tokens` table. Refresh tokens expire after
   90 days without use.
3. Register a webhook for `order.paid` pointing at
   `https://<your-app>.koyeb.app/webhooks/etsy` and copy its signing secret
   into `ETSY_WEBHOOK_SECRET`.

### 3. Backend on Koyeb

Create a service from this repo with the **Dockerfile** builder (build
context: repo root), instance type **free (512 MB)**, port **8000**, health
check `GET /health`, and the environment variables from
`backend/.env.example`. `PUBLIC_URL` is the service's own `*.koyeb.app` URL.

Local image check: `docker build -t cbn-backend . && docker run --env-file backend/.env -p 8000:8000 cbn-backend`.

### 4. Frontend on Vercel

Import the repo, set **Root Directory** to `frontend`, and set
`NEXT_PUBLIC_API_URL` to the Koyeb URL. Set the backend's `FRONTEND_URL` to
the Vercel URL (it is used for CORS and for the emailed link).

## Memory on the 512 MB instance

- Uploads stream straight to disk; Node never buffers an image.
- Only one Python process runs at a time; later uploads wait in a queue.
- Node's heap is capped at 160 MB (`NODE_OPTIONS`); idle RSS is ~125 MB.
- Python runs single-threaded (`OMP_NUM_THREADS=1` etc.), with
  `MALLOC_ARENA_MAX=2`, and is SIGKILLed after `PROCESS_TIMEOUT_SEC`.
- Prisma 7 uses the `pg` driver adapter (no Rust query engine), with a
  3-connection pool.
- The mock script decodes JPEGs at reduced size and refuses images over 40 MP.
  Keep the real script inside the remaining ~300 MB: downscale before
  clustering, and free large arrays early.

## Known limits

- **Output files live on the container's disk** (`DATA_DIR`), which Koyeb
  wipes on every redeploy or restart; old download links then return 410.
  Move them to object storage (S3, R2, Supabase Storage) to keep them.
- Buyers can pick any options; the selection isn't checked against what
  they paid for on Etsy.
- Jobs are queued in memory. If the container restarts mid-job, that order
  is marked `FAILED` at startup and the buyer is asked to upload again.
- Email is mocked (`backend/src/lib/email.ts` only logs).
- If marking the receipt shipped on Etsy fails, the buyer still gets the
  files; the error is stored in `orders.etsy_error` and `etsy_shipped_at`
  stays null, so those orders can be found and retried.

## Plugging in the real processor

```
python3 process_image.py INPUT OUTPUT_DIR --format dark --format procreate ...
```

The script must:

- write each output file into `OUTPUT_DIR`, plus `OUTPUT_DIR/manifest.json`:
  `[{"file": "dark-numbered.pdf", "label": "Dark Numbered Version (PDF)", "format": "dark"}, ...]`.
  Only plain file names listed there are ever served.
- print `PROGRESS <0-100> <message>` lines on stdout; the message is shown
  to the buyer under the progress bar.
- exit 0 on success, or non-zero with the reason on stderr.

All formats run in one Python process, so load the photo and compute the
palette once and reuse them (the mock does this). The image already contains
`cbn/` (on `PYTHONPATH`) and its dependencies, so the script can import
from `cbn` directly.
