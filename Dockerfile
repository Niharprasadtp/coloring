# Fulfillment backend for Koyeb: Fastify (Node 24) + Python image processing.
# Build from the repo root so the image also carries cbn/ for the real
# color-by-number logic:  docker build -t cbn-backend .

# ---- Build: compile TypeScript and generate the Prisma client ----
FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY backend/package.json backend/package-lock.json ./
RUN npm ci
COPY backend/tsconfig.json backend/prisma.config.ts ./
COPY backend/prisma ./prisma
COPY backend/src ./src
# prisma generate reads the config but never connects; any URL will do.
RUN DIRECT_URL=postgresql://build@localhost/build npm run build && npm prune --omit=dev

# ---- Runtime ----
FROM node:24-bookworm-slim
# libglib2.0-0 is the one shared library opencv-python-headless still needs;
# Pillow and numpy wheels bundle the rest.
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Python deps in a venv (Debian blocks system-wide pip installs). The mock only
# needs Pillow; the rest is what cbn/ needs once the real logic is wired in.
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv \
 && grep -v '^pytest' /tmp/requirements.txt > /tmp/req-prod.txt \
 && /opt/venv/bin/pip install --no-cache-dir Pillow -r /tmp/req-prod.txt \
 && rm /tmp/requirements.txt /tmp/req-prod.txt

WORKDIR /app
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY backend/package.json ./
COPY backend/scripts ./scripts
COPY cbn ./cbn

# Memory tuning for Koyeb's 512 MB instance:
# - cap V8's heap so Node leaves room for the Python child process
# - fewer glibc malloc arenas, and single-threaded math libs in Python
ENV NODE_ENV=production \
    NODE_OPTIONS=--max-old-space-size=160 \
    MALLOC_ARENA_MAX=2 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PYTHON_BIN=/opt/venv/bin/python \
    DATA_DIR=/tmp/cbn-data \
    PORT=8000

USER node
EXPOSE 8000
CMD ["node", "dist/server.js"]
