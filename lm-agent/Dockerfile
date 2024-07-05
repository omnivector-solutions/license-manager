FROM python:3.12.3-slim-bullseye

WORKDIR /app

RUN apt update && apt install -y curl libpq-dev gcc

COPY . /app/lm-agent

RUN python -m venv /srv/license-manager-agent-venv
RUN /srv/license-manager-agent-venv/bin/pip install /app/lm-agent

CMD ["tail", "-f", "/dev/null"]
