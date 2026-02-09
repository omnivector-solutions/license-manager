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

# Default simulator API port
LM_SIM_PORT="${LM_SIM_PORT:-8080}"
LM_SIM_HOST="${LM_SIM_HOST:-127.0.0.1}"

# Check if ENABLE_LM_SIMULATOR is set to true (case-insensitive)
if [[ "${ENABLE_LM_SIMULATOR,,}" == "true" ]]; then
    echo "LM Simulator is enabled"
    
    # Configure simulator API to use SQLite
    export DATABASE_TYPE="${DATABASE_TYPE:-sqlite}"
    export SQLITE_PATH="${SQLITE_PATH:-/app/data/simulator.db}"
    
    echo "Starting LM Simulator API on ${LM_SIM_HOST}:${LM_SIM_PORT}..."
    echo "  DATABASE_TYPE=$DATABASE_TYPE"
    echo "  SQLITE_PATH=$SQLITE_PATH"
    
    # Start the simulator API in the background (use app which includes lifespan for db init)
    uvicorn lm_simulator_api.main:app \
        --host "${LM_SIM_HOST}" \
        --port "${LM_SIM_PORT}" \
        --log-level info &
    
    SIMULATOR_PID=$!
    echo "Simulator API started with PID $SIMULATOR_PID"
    
    # Wait for simulator API to be ready
    echo "Waiting for Simulator API to be ready..."
    for i in {1..30}; do
        if curl -s "http://${LM_SIM_HOST}:${LM_SIM_PORT}/lm-sim/health" > /dev/null 2>&1; then
            echo "Simulator API is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "WARNING: Simulator API may not be ready after 30 seconds"
        fi
        sleep 1
    done
    
    # Export simulator binary paths for lm-agent to use
    # These point to the lm-simulator fake binaries installed in the venv
    export LM_AGENT_LMUTIL_PATH="${LM_AGENT_LMUTIL_PATH:-lmutil}"
    export LM_AGENT_RLMUTIL_PATH="${LM_AGENT_RLMUTIL_PATH:-rlmutil}"
    export LM_AGENT_LSDYNA_PATH="${LM_AGENT_LSDYNA_PATH:-lstc_qrun}"
    export LM_AGENT_LMXENDUTIL_PATH="${LM_AGENT_LMXENDUTIL_PATH:-lmxendutil}"
    export LM_AGENT_OLIXTOOL_PATH="${LM_AGENT_OLIXTOOL_PATH:-olixtool}"
    
    echo "Simulator binaries configured:"
    echo "  LM_AGENT_LMUTIL_PATH=$LM_AGENT_LMUTIL_PATH"
    echo "  LM_AGENT_RLMUTIL_PATH=$LM_AGENT_RLMUTIL_PATH"
    echo "  LM_AGENT_LSDYNA_PATH=$LM_AGENT_LSDYNA_PATH"
    echo "  LM_AGENT_LMXENDUTIL_PATH=$LM_AGENT_LMXENDUTIL_PATH"
    echo "  LM_AGENT_OLIXTOOL_PATH=$LM_AGENT_OLIXTOOL_PATH"
else
    echo "LM Simulator is disabled"
fi

# Default prolog/epilog API port
LM_PROLOG_EPILOG_PORT="${LM_PROLOG_EPILOG_PORT:-8081}"
LM_PROLOG_EPILOG_HOST="${LM_PROLOG_EPILOG_HOST:-0.0.0.0}"

# Check if ENABLE_PROLOG_EPILOG_API is set to true (case-insensitive)
if [[ "${ENABLE_PROLOG_EPILOG_API,,}" == "true" ]]; then
    echo "Prolog/Epilog API is enabled"
    
    echo "Starting Prolog/Epilog API on ${LM_PROLOG_EPILOG_HOST}:${LM_PROLOG_EPILOG_PORT}..."
    
    # Start the prolog/epilog API in the background
    uvicorn lm_prolog_epilog_api.main:app \
        --host "${LM_PROLOG_EPILOG_HOST}" \
        --port "${LM_PROLOG_EPILOG_PORT}" \
        --log-level info &
    
    PROLOG_EPILOG_PID=$!
    echo "Prolog/Epilog API started with PID $PROLOG_EPILOG_PID"
    
    # Wait for prolog/epilog API to be ready
    echo "Waiting for Prolog/Epilog API to be ready..."
    for i in {1..30}; do
        if curl -s "http://${LM_PROLOG_EPILOG_HOST}:${LM_PROLOG_EPILOG_PORT}/health" > /dev/null 2>&1; then
            echo "Prolog/Epilog API is ready!"
            break
        fi
        if [ $i -eq 30 ]; then
            echo "WARNING: Prolog/Epilog API may not be ready after 30 seconds"
        fi
        sleep 1
    done
else
    echo "Prolog/Epilog API is disabled"
fi

echo "---> Polutating LM API with pre-defined license ..."
if [ -f /app/populate-lm-api.py ]; then
    /app/populate-lm-api.py
else
    echo "WARNING: /app/populate-lm-api.py not found, skipping LM API population"
fi

echo "---> Polutating LM Simulator API with pre-defined license ..."
if [ -f /app/populate-lm-simulator-api.py ]; then
    /app/populate-lm-simulator-api.py
else
    echo "WARNING: /app/populate-lm-simulator-api.py not found, skipping LM Simulator API population"
fi

echo "Starting License Manager Agent..."
exec license-manager-agent "$@"
