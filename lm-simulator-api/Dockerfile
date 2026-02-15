FROM ubuntu:resolute AS builder

WORKDIR /app

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace configuration and lock file from root
COPY ./pyproject.toml ./uv.lock /app/

# Copy lm-simulator-api package
COPY ./lm-simulator-api/pyproject.toml ./lm-simulator-api/README.md /app/lm-simulator-api/
COPY ./lm-simulator-api/lm_simulator_api /app/lm-simulator-api/lm_simulator_api

# Install dependencies with Python in a portable location
ENV UV_PYTHON_INSTALL_DIR=/app/.python
RUN uv sync --frozen --no-dev --no-editable --package license-manager-simulator-api


FROM ubuntu:resolute AS runner

WORKDIR /app

# Install curl for health checks
RUN apt update && apt install -y curl && rm -rf /var/lib/apt/lists/*

# Copy virtual environment and uv-managed Python from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.python /app/.python

ENV PATH="/app/.venv/bin:$PATH"

# Create data directory for SQLite
RUN mkdir -p /app/data

CMD ["/app/.venv/bin/uvicorn", "lm_simulator_api.main:app", "--host", "0.0.0.0", "--port", "80", "--loop", "asyncio"]
