#!/bin/bash
# slurmctld_epilog.sh - License Manager Epilog
# Removes job bookings from the license-manager API after job completion.
# Always exits 0 -- epilog failures should not affect job completion.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source configuration and shared helpers
# shellcheck source=/dev/null
source "${LM_CONFIG_FILE:-/etc/default/license-manager}"
# shellcheck source=acquire_oidc_token.sh
source "${SCRIPT_DIR}/acquire_oidc_token.sh"

# --- Environment variables from Slurm ---
JOB_ID="${SLURM_JOB_ID}"
JOB_LICENSES="${SLURM_JOB_LICENSES:-}"

# Exit early if no licenses were requested
if [[ -z "$JOB_LICENSES" || "$JOB_LICENSES" == "(null)" ]]; then
    exit 0
fi

# Exit early if no tracked licenses (product.feature@server_type) are requested
if ! echo "$JOB_LICENSES" | grep -qE '[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+@'; then
    exit 0
fi

# --- Acquire OIDC token ---
if ! TOKEN="$(acquire_oidc_token)"; then
    logger -t "lm-epilog" "Could not acquire OIDC token; bookings for job ${JOB_ID} were not released"
    exit 0
fi

# --- Remove job bookings ---
if ! http_request DELETE "${LM_API_BASE_URL}/lm/jobs/slurm_job_id/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}"; then
    logger -t "lm-epilog" "Failed to remove bookings for job ${JOB_ID} (request error)"
elif [[ "$HTTP_CODE" -ne 200 && "$HTTP_CODE" -ne 404 ]]; then
    logger -t "lm-epilog" "Failed to remove bookings for job ${JOB_ID} (HTTP ${HTTP_CODE})"
else
    logger -t "lm-epilog" "Booking removed for licenses ${JOB_LICENSES} from job ${JOB_ID}"
fi

# Exit 0 to not block job completion
exit 0
