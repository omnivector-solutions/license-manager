FROM ubuntu:resolute AS builder

WORKDIR /app

# Copy uv from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy workspace configuration and lock file from root
COPY ./pyproject.toml ./uv.lock /app/

# Copy lm-prolog-epilog-api package
COPY ./lm-prolog-epilog-api /app/lm-prolog-epilog-api

# Copy lm-agent package (workspace dependency)
COPY ./lm-agent /app/lm-agent

# Install dependencies with Python in a portable location
ENV UV_PYTHON_INSTALL_DIR=/app/.python
RUN uv sync --frozen --no-dev --python 3.12 --managed-python \
    --no-editable --package license-manager-prolog-epilog-api


FROM ubuntu:resolute AS runner

WORKDIR /app

# Install curl for health checks
RUN apt update && apt install -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 401 -r slurm \
    && useradd -r -u 401 -g 401 slurm

# Copy virtual environment and uv-managed Python from builder
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/.python /app/.python

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8081

CMD ["/app/.venv/bin/uvicorn", "lm_prolog_epilog_api.main:app", "--host", "0.0.0.0", "--port", "8081"]
