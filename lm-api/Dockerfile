FROM python:3.12.3-slim-bullseye as builder

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc
RUN pip install poetry==1.4.0

COPY ./pyproject.toml ./poetry.lock /app

RUN poetry config virtualenvs.in-project true \
    && poetry install --no-root --no-dev \
    && rm -rf "$POETRY_CACHE_DIR"


FROM python:3.12.3-slim-bullseye as runner

WORKDIR /app

RUN apt update && apt install -y curl

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

COPY ./alembic /app/alembic
COPY ./lm_api /app/lm_api

CMD ["uvicorn", "lm_api.main:app", "--host", "0.0.0.0", "--port", "7000", "--loop", "asyncio"]
