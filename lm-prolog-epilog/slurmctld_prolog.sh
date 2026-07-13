#!/bin/bash
# slurmctld_prolog.sh - License Manager Prolog
# Makes a booking request to the License Manager API for tracked licenses.
# Exit 0 = job proceeds, Exit 1 = job rejected.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source configuration and shared helpers
# shellcheck source=/dev/null
source "${LM_CONFIG_FILE:-/etc/default/license-manager-agent}"
# shellcheck source=acquire_oidc_token.sh
source "${SCRIPT_DIR}/acquire_oidc_token.sh"

# --- Environment variables from Slurm ---
JOB_ID="${SLURM_JOB_ID}"
JOB_USER="${SLURM_JOB_USER}"
JOB_NODELIST="${SLURM_JOB_NODELIST}"
JOB_LICENSES="${SLURM_JOB_LICENSES:-}"

# Exit early if no licenses requested
if [[ -z "$JOB_LICENSES" || "$JOB_LICENSES" == "(null)" ]]; then
    exit 0
fi

# --- Parse licenses into JSON bookings ---
# Format: product.feature@server_type:quantity,...
BOOKINGS=""
IFS=',' read -ra LICENSE_ARRAY <<< "$JOB_LICENSES"
for lic in "${LICENSE_ARRAY[@]}"; do
    if [[ "$lic" =~ ^([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)@([a-zA-Z0-9_]+)(:([0-9]+))?$ ]]; then
        PRODUCT="${BASH_REMATCH[1]}"
        FEATURE="${BASH_REMATCH[2]}"
        QUANTITY="${BASH_REMATCH[5]:-1}"
        [[ -n "$BOOKINGS" ]] && BOOKINGS+=","
        BOOKINGS+="{\"product_feature\":\"${PRODUCT}.${FEATURE}\",\"quantity\":${QUANTITY}}"
    fi
done

# Exit if no parseable licenses
if [[ -z "$BOOKINGS" ]]; then
    exit 0
fi

# --- Resolve lead host ---
LEAD_HOST="$("${SCONTROL_PATH:-/usr/bin/scontrol}" show hostnames "$JOB_NODELIST" | head -1)"
if [[ -z "$LEAD_HOST" ]]; then
    log CRITICAL "Could not resolve lead host for job ${JOB_ID}; rejecting"
    exit 1
fi

# --- Acquire OIDC token ---
if ! TOKEN="$(acquire_oidc_token)"; then
    logger -t "lm-prolog" "Could not acquire OIDC token for job ${JOB_ID}; rejecting"
    exit 1
fi

# --- Make booking request ---
PAYLOAD="{\"slurm_job_id\":\"${JOB_ID}\",\"username\":\"${JOB_USER}\",\"lead_host\":\"${LEAD_HOST}\",\"bookings\":[${BOOKINGS}]}"

if http_request POST "${LM_API_BASE_URL}/lm/jobs" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" && [[ "$HTTP_CODE" -eq 201 ]]; then
    logger -t "lm-prolog" "Booking acquired for job ${JOB_ID} from user ${JOB_USER}, booked licenses: ${JOB_LICENSES})"
    exit 0
fi

logger -t "lm-prolog" "Booking request for job ${JOB_ID} failed with ${HTTP_CODE}: ${HTTP_BODY}"
exit 1
