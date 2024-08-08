FROM python:3.12-slim-bullseye

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

COPY ./pyproject.toml ./poetry.lock* /app/

RUN pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --no-dev \
    && rm -rf "$POETRY_CACHE_DIR"

ENV PATH="/app/.venv/bin:$PATH"

COPY ./lm_simulator_api /app/lm_simulator_api

CMD ["uvicorn", "lm_simulator_api.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
