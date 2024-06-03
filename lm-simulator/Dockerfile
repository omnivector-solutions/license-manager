FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-slim

ENV MODULE_NAME=lm_simulator.main

RUN apt update && apt install -y curl libpq-dev gcc

RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY ./pyproject.toml ./poetry.lock* /app/

RUN poetry install --no-root --only main

COPY ./lm_simulator /app/lm_simulator