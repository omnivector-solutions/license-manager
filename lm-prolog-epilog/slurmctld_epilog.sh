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

# --- Parse requested licenses ---
# Format: product.feature@server_type:quantity,...
declare -a REQUESTED_FEATURES=()
IFS=',' read -ra LICENSE_ARRAY <<< "$JOB_LICENSES"
for lic in "${LICENSE_ARRAY[@]}"; do
    if [[ "$lic" =~ ^([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)@([a-zA-Z0-9_]+)(:([0-9]+))?$ ]]; then
        REQUESTED_FEATURES+=("${BASH_REMATCH[1]}.${BASH_REMATCH[2]}")
    fi
done

# Exit early if no tracked licenses (product.feature@server_type) are requested
if [[ ${#REQUESTED_FEATURES[@]} -eq 0 ]]; then
    exit 0
fi

# --- Acquire OIDC token ---
if ! TOKEN="$(acquire_oidc_token)"; then
    logger -t "lm-epilog" "Could not acquire OIDC token; bookings for job ${JOB_ID} were not released"
    exit 0
fi

# --- Fetch the licenses tracked by License Manager for this cluster ---
# Only licenses configured in the API can have bookings, so filter the requested
# licenses to the tracked ones to report an accurate list.
BOOKED_LICENSES=""
if http_request GET "${LM_API_BASE_URL}/lm/configurations/by_client_id" \
    -H "Authorization: Bearer ${TOKEN}" && [[ "$HTTP_CODE" -eq 200 ]]; then
    TRACKED_FEATURES="$(
        printf '%s' "$HTTP_BODY" \
            | grep -oE '"name":"[^"]+","product":\{"id":[0-9]+,"name":"[^"]+"' \
            | sed -E 's/"name":"([^"]+)","product":\{"id":[0-9]+,"name":"([^"]+)"/\2.\1/' || true
    )"
    for feature in "${REQUESTED_FEATURES[@]}"; do
        if grep -qxF "$feature" <<< "$TRACKED_FEATURES"; then
            [[ -n "$BOOKED_LICENSES" ]] && BOOKED_LICENSES+=","
            BOOKED_LICENSES+="${feature}"
        fi
    done
fi

# Exit if none of the requested licenses are tracked
if [[ -z "$BOOKED_LICENSES" ]]; then
    exit 0
fi

# --- Remove job bookings ---
if ! http_request DELETE "${LM_API_BASE_URL}/lm/jobs/slurm_job_id/${JOB_ID}" \
    -H "Authorization: Bearer ${TOKEN}"; then
    logger -t "lm-epilog" "Failed to remove bookings for job ${JOB_ID} (request error)"
elif [[ "$HTTP_CODE" -ne 200 && "$HTTP_CODE" -ne 404 ]]; then
    logger -t "lm-epilog" "Failed to remove bookings for job ${JOB_ID} (HTTP ${HTTP_CODE})"
else
    logger -t "lm-epilog" "Bookings released for job ${JOB_ID} (licenses: ${BOOKED_LICENSES})"
fi

# Exit 0 to not block job completion
exit 0
