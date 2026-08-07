FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates munge slurm-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN mkdir -p /var/log/license-manager-agent /var/cache/license-manager-agent \
    && chmod -R 777 /var/log/license-manager-agent /var/cache/license-manager-agent

WORKDIR /app/lm-agent

COPY pyproject.toml uv.lock README.md ./
COPY lm_agent ./lm_agent

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "license-manager-agent"]
