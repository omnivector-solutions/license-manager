#!/bin/bash
set -e

# Function to handle shutdown
cleanup() {
    echo "Shutting down..."
    # Kill all child processes
    pkill -P $$ || true
    exit 0
}

trap cleanup SIGTERM SIGINT

echo "Starting License Manager API..."
exec uvicorn lm_api.main:app --host 0.0.0.0 --port 8000 --loop asyncio "$@"