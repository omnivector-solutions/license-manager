#!/bin/bash
set -e

# Set LD_LIBRARY_PATH for Slurm binaries only
export SLURM_LD_LIBRARY_PATH="/opt/slurm/view/lib/private:/opt/slurm/view/lib:/opt/slurm/view/lib/slurm"

# Start sackd for Slurm authentication if available
if [[ -x "/opt/slurm/view/sbin/sackd" ]]; then
    echo "Starting sackd for Slurm authentication..."
    LD_LIBRARY_PATH="$SLURM_LD_LIBRARY_PATH" /opt/slurm/view/sbin/sackd &
    SACKD_PID=$!
    echo "sackd started with PID $SACKD_PID"
    sleep 1
fi

# Execute the original entrypoint
exec /app/entrypoint.sh "$@"
