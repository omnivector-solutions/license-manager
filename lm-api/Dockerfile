FROM ubuntu AS builder
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt update \
    && apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev \
       libssl-dev libreadline-dev libffi-dev libsqlite3-dev wget libbz2-dev libpq-dev -y \
    && wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz \
    && tar -xf Python-3.12.0.tgz \
    && cd Python-3.12.*/ \
    && ./configure --enable-optimizations \
    && make \
    && make altinstall

ENV PATH="/opt/venv/bin:$PATH"

COPY ./README.md ./pyproject.toml ./poetry.lock* /app/
COPY ./lm_api /app/lm_api

RUN pip3.12 install .

FROM ubuntu AS runner
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /usr/local/bin/python3.12 /usr/local/bin/

COPY ./lm_api /app/lm_api
COPY ./alembic /app/alembic

ENV PATH="/opt/venv/bin:$PATH"

CMD ["uvicorn", "lm_api.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
