FROM python:3.12-slim-bullseye as builder

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

COPY ./pyproject.toml ./uv.lock ./README.md /app/

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN uv sync --frozen --no-dev


FROM python:3.12-slim-bullseye as runner

WORKDIR /app

RUN apt update && apt install -y curl libpq5

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

COPY ./alembic /app/alembic
COPY ./lm_api /app/lm_api
COPY ./entrypoint.sh /app/lm-api-entrypoint.sh

ENTRYPOINT ["/bin/bash", "/app/lm-api-entrypoint.sh"]
