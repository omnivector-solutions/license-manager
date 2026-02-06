#!/bin/bash
#
# Slurm PrologSlurmctld script for license-manager
#
# This script is called by slurmctld when a job starts.
# It reads job context from Slurm environment variables and calls the
# license-manager prolog API endpoint.
#
# Required Slurm environment variables:
#   SLURM_CLUSTER_NAME - Name of the cluster
#   SLURM_JOB_ID       - Job ID
#   SLURM_JOB_NODELIST - List of nodes allocated to the job
#   SLURM_JOB_USER     - Username of the job owner
#   SLURM_JOB_LICENSES - Licenses requested by the job (optional)
#
# Configuration environment variables:
#   LM_PROLOG_EPILOG_API_URL - Base URL for the prolog/epilog API (default: http://localhost:8081)
#

set -e

# Configuration
LM_PROLOG_EPILOG_API_URL="${LM_PROLOG_EPILOG_API_URL:-http://localhost:8081}"

# Log function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] PROLOG: $*" >&2
}

# Get lead host from nodelist (simplified - takes first node)
get_lead_host() {
    local nodelist="$1"
    # Handle simple cases like "node001" or "node[001-003]"
    # For bracketed notation, extract the first node
    if [[ "$nodelist" =~ \[([0-9]+) ]]; then
        local prefix="${nodelist%%\[*}"
        local first_num="${BASH_REMATCH[1]}"
        echo "${prefix}${first_num}"
    else
        # Just return the first comma-separated node
        echo "${nodelist%%,*}"
    fi
}

# Validate required environment variables
validate_env() {
    local missing=()
    
    [[ -z "${SLURM_CLUSTER_NAME:-}" ]] && missing+=("SLURM_CLUSTER_NAME")
    [[ -z "${SLURM_JOB_ID:-}" ]] && missing+=("SLURM_JOB_ID")
    [[ -z "${SLURM_JOB_NODELIST:-}" ]] && missing+=("SLURM_JOB_NODELIST")
    [[ -z "${SLURM_JOB_USER:-}" ]] && missing+=("SLURM_JOB_USER")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log "ERROR: Missing required environment variables: ${missing[*]}"
        exit 1
    fi
}

# Main function
main() {
    log "Starting prolog for job ${SLURM_JOB_ID:-unknown}"
    
    # Validate environment
    validate_env
    
    # Get lead host
    local lead_host
    lead_host=$(get_lead_host "$SLURM_JOB_NODELIST")
    
    # Build JSON payload
    local payload
    payload=$(cat <<EOF
{
    "cluster_name": "${SLURM_CLUSTER_NAME}",
    "job_id": "${SLURM_JOB_ID}",
    "lead_host": "${lead_host}",
    "user_name": "${SLURM_JOB_USER}",
    "job_licenses": "${SLURM_JOB_LICENSES:-}"
}
EOF
)
    
    log "Calling prolog API at ${LM_PROLOG_EPILOG_API_URL}/prolog"
    log "Payload: $payload"
    
    # Call the API
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST "${LM_PROLOG_EPILOG_API_URL}/prolog" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --connect-timeout 10 \
        --max-time 30)
    
    # Extract HTTP code (last line) and body (everything else)
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    log "Response (HTTP $http_code): $body"
    
    # Check for success
    if [[ "$http_code" -ge 200 && "$http_code" -lt 300 ]]; then
        log "Prolog completed successfully for job ${SLURM_JOB_ID}"
        exit 0
    else
        log "ERROR: Prolog failed for job ${SLURM_JOB_ID} (HTTP $http_code)"
        exit 1
    fi
}

main "$@"
