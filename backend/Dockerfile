FROM ubuntu as builder
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt update \
    && apt install python3.11-venv python3.11-dev curl libpq-dev gcc -y \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3.11 - \
    && pip3 install wheel setuptools --upgrade

RUN python3.11 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

COPY ./README.rst ./pyproject.toml ./poetry.lock* /app/
COPY ./lm_backend /app/lm_backend
COPY ./alembic /app/alembic

RUN pip3 install .


FROM ubuntu
#RUN apt update \
#    && apt install python3.11 -y 
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpq.so.5.14 /usr/lib/x86_64-linux-gnu/
RUN ln -s /usr/lib/x86_64-linux-gnu/libpq.so.5.14 /usr/lib/x86_64-linux-gnu/libpq.so

WORKDIR /app/
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./lm_backend /app/lm_backend
COPY ./alembic /app/alembic

CMD ["uvicorn", "lm_backend.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
