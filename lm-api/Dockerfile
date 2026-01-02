FROM python:3.12-slim-bullseye as builder

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

COPY ./pyproject.toml ./uv.lock ./README.md /app/

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN uv sync --frozen --no-dev


FROM python:3.12-slim-bullseye as runner

WORKDIR /app

RUN apt update && apt install -y curl

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

COPY ./alembic /app/alembic
COPY ./lm_api /app/lm_api

CMD ["uvicorn", "lm_api.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
