FROM python:3.12-slim-bullseye AS builder

WORKDIR /app

RUN apt update && apt install -y curl

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace configuration and lock file from root
COPY ./pyproject.toml ./uv.lock /app/

# Copy lm-agent package (including source for proper installation)
COPY ./lm-agent/pyproject.toml ./lm-agent/README.md /app/lm-agent/
COPY ./lm-agent/lm_agent /app/lm-agent/lm_agent

# Copy lm-simulator package (including source for proper installation)
COPY ./lm-simulator/pyproject.toml ./lm-simulator/README.md /app/lm-simulator/
COPY ./lm-simulator/lm_simulator /app/lm-simulator/lm_simulator

# Install all dependencies and workspace packages
RUN uv sync --frozen --no-dev


FROM python:3.12-slim-bullseye AS runner

WORKDIR /app

RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app /app

ENV PATH="/app/.venv/bin:$PATH"

# Copy entrypoint script
COPY ./lm-agent/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Environment variable to conditionally enable lm-simulator
ENV ENABLE_LM_SIMULATOR=false

ENTRYPOINT ["/app/entrypoint.sh"]
