FROM python:3.12-slim-bullseye as builder

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

COPY ./pyproject.toml ./poetry.lock /app

RUN pip install poetry==2.1.2 \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --only main \
    && rm -rf "$POETRY_CACHE_DIR"

FROM python:3.12-slim-bullseye as runner

WORKDIR /app

RUN apt update && apt install -y curl

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

COPY ./alembic /app/alembic
COPY ./lm_api /app/lm_api

CMD ["uvicorn", "lm_api.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
