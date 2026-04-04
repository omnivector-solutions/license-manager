FROM ubuntu:resolute AS builder

WORKDIR /app

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy lm-simulator-api package
COPY ./lm-simulator-api/pyproject.toml ./lm-simulator-api/uv.lock ./lm-simulator-api/README.md /app/
COPY ./lm-simulator-api/lm_simulator_api /app/lm_simulator_api

# Install dependencies with Python in a portable location
ENV UV_PYTHON_INSTALL_DIR=/app/.python
RUN uv sync --python 3.12 --managed-python --frozen --no-dev --no-editable


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
EXPOSE 8000

CMD ["/app/.venv/bin/uvicorn", "lm_simulator_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "asyncio"]
