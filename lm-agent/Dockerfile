FROM ubuntu:resolute AS builder

WORKDIR /app

RUN apt update && apt install -y curl

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace configuration and lock file from root
COPY ./pyproject.toml ./uv.lock /app/

# Copy workspace packages (entire directories like jobbergate does)
COPY ./lm-agent /app/lm-agent
COPY ./lm-simulator /app/lm-simulator
COPY ./lm-simulator-api /app/lm-simulator-api
COPY ./lm-prolog-epilog-api /app/lm-prolog-epilog-api

# Install all workspace packages with Python in a portable location
ENV UV_PYTHON_INSTALL_DIR=/app/.python
RUN uv sync --python 3.12 --managed-python --frozen --no-dev --no-editable

FROM ubuntu:resolute AS runner

WORKDIR /app

# Install curl for health checks + tzdata
RUN apt update && apt install -y curl tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 401 -r slurm \
    && useradd -r -u 401 -g 401 slurm

# Copy virtual environment and uv-managed Python from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.python /app/.python

ENV PATH="/app/.venv/bin:$PATH"

# Create log directory for the agent and data directory for SQLite
RUN mkdir -p /var/log/license-manager-agent /app/data

# Copy entrypoint script
COPY ./lm-agent/entrypoint.sh /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
