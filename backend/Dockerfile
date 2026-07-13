FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . ./
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["sh", "-c", "uv run fastapi run --entrypoint boutique.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
