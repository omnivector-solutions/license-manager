#!/bin/bash
set -e

echo "---> Polutating LM Simulator API with pre-defined license ..."
if [ -f /app/populate-lm-simulator-api.py ]; then
    /app/.venv/bin/python /app/populate-lm-simulator-api.py
else
    echo "WARNING: /app/populate-lm-simulator-api.py not found, skipping LM Simulator API population"
fi

echo "Starting License Manager Simulator API..."
exec uvicorn lm_simulator_api.main:app --workers 1 --host 0.0.0.0 --port 8000