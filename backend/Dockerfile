FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

ENV MODULE_NAME=lm_backend.main

RUN apt update && apt install -y curl

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry POETRY_VERSION=1.1.13 python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root --no-dev

COPY ./lm_backend /app/lm_backend