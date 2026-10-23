FROM node:22-bookworm-slim AS frontend
WORKDIR /frontend
COPY ai-research-frontend/package*.json ./
RUN npm ci
COPY ai-research-frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PYTHONUTF8=1
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY --from=frontend /frontend/build ./frontend
ENV FRONTEND_DIST=/app/frontend COOKIE_SECURE=true
CMD ["sh", "-c", "exec /app/.venv/bin/python -m uvicorn src.api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
