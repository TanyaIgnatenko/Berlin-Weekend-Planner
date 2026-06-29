# Single-image deploy: build the SPA, then run FastAPI which serves BOTH the
# /api routes and the built web/dist on one origin (no CORS, no proxy needed).
# Railway auto-detects this Dockerfile.

# --- stage 1: build the React/TS frontend -> /web/dist ---
FROM node:20-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# --- stage 2: python backend + the built SPA ---
FROM python:3.12-slim
WORKDIR /app

# lean runtime deps only (skip the optional arize-phoenix tracing stack;
# init_tracing() fails open when it's absent)
RUN pip install --no-cache-dir \
    "langgraph>=0.2" "litellm>=1.40" "pydantic>=2.6" "requests>=2.31" \
    "fastapi>=0.110" "uvicorn[standard]>=0.29" "sse-starlette>=2.0"

COPY src/ ./src/
COPY data/ ./data/
# app.py resolves web/dist relative to the repo root (parents[2]) -> /app/web/dist
COPY --from=web /web/dist ./web/dist

# default to the keyless demo scenario; override in Railway for real planning
ENV PLANNER_SEED_MODE=1
EXPOSE 8000

# Railway injects $PORT; fall back to 8000 locally
CMD ["sh", "-c", "uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
