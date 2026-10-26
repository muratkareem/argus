FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY backend ./backend
COPY scripts ./scripts
RUN useradd --create-home argus && mkdir -p /app/ml/artifacts && chown -R argus:argus /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/backend
USER argus
EXPOSE 8000
CMD ["sh", "scripts/entrypoint.sh"]
