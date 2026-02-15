FROM ubuntu:resolute AS builder

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

# Copy lm-simulator-api package (including source for proper installation)
COPY ./lm-simulator-api/pyproject.toml ./lm-simulator-api/README.md /app/lm-simulator-api/
COPY ./lm-simulator-api/lm_simulator_api /app/lm-simulator-api/lm_simulator_api

# Copy lm-prolog-epilog-api package (including source for proper installation)
COPY ./lm-prolog-epilog-api/pyproject.toml ./lm-prolog-epilog-api/README.md /app/lm-prolog-epilog-api/
COPY ./lm-prolog-epilog-api/lm_prolog_epilog_api /app/lm-prolog-epilog-api/lm_prolog_epilog_api

# Install all dependencies and workspace packages with Python in a portable location
ENV UV_PYTHON_INSTALL_DIR=/app/.python
RUN uv sync --frozen --no-dev


FROM ubuntu:resolute AS runner

WORKDIR /app

# Install curl for health checks
RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

# Create slurm user (needed for Slurm client commands to read slurm.conf)
RUN groupadd -r slurm && useradd -r -g slurm slurm

# Copy virtual environment and uv-managed Python from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.python /app/.python

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
