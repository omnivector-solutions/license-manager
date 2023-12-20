FROM python:3.12-slim-bullseye

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

RUN curl -sSL https://install.python-poetry.org | \
    POETRY_HOME=/opt/poetry POETRY_VERSION=1.4.0 python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root --no-dev

COPY ./alembic /app/alembic
COPY ./lm_backend /app/lm_backend

CMD ["uvicorn", "lm_backend.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
