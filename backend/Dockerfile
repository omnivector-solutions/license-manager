FROM python:3.8 as requirements-stage

WORKDIR /tmp

RUN pip install poetry
COPY ./pyproject.toml ./poetry.lock* /tmp/
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.8

RUN apt-get -y update
RUN apt-get install -y --fix-missing build-essential cmake libpq-dev

WORKDIR /app

COPY --from=requirements-stage /tmp/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


COPY . /app
RUN pip install .
CMD ["uvicorn", "lm_backend.main:app", "--host", "0.0.0.0", "--port", "80"]
