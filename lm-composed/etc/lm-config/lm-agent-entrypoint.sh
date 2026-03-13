#!/bin/bash
set -e

echo "---> Polutating LM API with pre-defined license ..."
if [ -f /app/populate-lm-api.py ]; then
    /app/.venv/bin/python /app/populate-lm-api.py
else
    echo "WARNING: /app/populate-lm-api.py not found, skipping LM API population"
fi

echo "---> Polutating LM Simulator API with pre-defined license ..."
if [ -f /app/populate-lm-simulator-api.py ]; then
    /app/.venv/bin/python /app/populate-lm-simulator-api.py
else
    echo "WARNING: /app/populate-lm-simulator-api.py not found, skipping LM Simulator API population"
fi

echo "Starting License Manager Agent..."
exec /app/.venv/bin/license-manager-agent "$@"