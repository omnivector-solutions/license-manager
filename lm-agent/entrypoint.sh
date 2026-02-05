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

# Check if ENABLE_LM_SIMULATOR is set to true (case-insensitive)
if [[ "${ENABLE_LM_SIMULATOR,,}" == "true" ]]; then
    echo "LM Simulator is enabled"
    
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

echo "Starting License Manager Agent..."
exec license-manager-agent "$@"
