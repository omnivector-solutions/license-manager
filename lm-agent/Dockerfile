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
RUN uv sync --frozen --no-dev --no-editable


FROM ubuntu:resolute AS runner

WORKDIR /app

# Install curl for health checks and tzdata for timezone support
RUN apt update && apt install -y curl tzdata && rm -rf /var/lib/apt/lists/*

# Create slurm user (needed for Slurm client commands to read slurm.conf)
RUN groupadd -r slurm && useradd -r -g slurm slurm

# Copy virtual environment and uv-managed Python from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.python /app/.python

ENV PATH="/app/.venv/bin:$PATH"

# Create log directory for the agent and data directory for SQLite
RUN mkdir -p /var/log/license-manager-agent /app/data

# Copy entrypoint script
COPY ./lm-agent/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Environment variable to conditionally enable lm-simulator
ENV ENABLE_LM_SIMULATOR=false

# Environment variable to conditionally enable prolog/epilog API
ENV ENABLE_PROLOG_EPILOG_API=false

# Simulator API port (when enabled)
EXPOSE 8080

# Prolog/Epilog API port (when enabled)
EXPOSE 8081

ENTRYPOINT ["/app/entrypoint.sh"]
