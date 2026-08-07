#!/bin/bash
# slurmctld_prolog.sh - License Manager Prolog
# Makes a booking request to the License Manager API for tracked licenses.
# Exit 0 = job proceeds, Exit 1 = job rejected.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source configuration and shared helpers
# shellcheck source=/dev/null
source "${LM_CONFIG_FILE:-/etc/default/license-manager}"
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

# --- Parse requested licenses ---
# Format: product.feature@server_type:quantity,...
declare -a REQUESTED_PRODUCT_FEATURES=()
declare -a REQUESTED_QUANTITIES=()
declare -a REQUESTED_LICENSES=()
IFS=',' read -ra LICENSE_ARRAY <<< "$JOB_LICENSES"
for lic in "${LICENSE_ARRAY[@]}"; do
    if [[ "$lic" =~ ^([a-zA-Z0-9_-]+)\.([a-zA-Z0-9_-]+)@([a-zA-Z0-9_]+)(:([0-9]+))?$ ]]; then
        REQUESTED_PRODUCT_FEATURES+=("${BASH_REMATCH[1]}.${BASH_REMATCH[2]}")
        REQUESTED_QUANTITIES+=("${BASH_REMATCH[5]:-1}")
        REQUESTED_LICENSES+=("$lic")
    fi
done

# Exit if no parseable licenses
if [[ ${#REQUESTED_PRODUCT_FEATURES[@]} -eq 0 ]]; then
    exit 0
fi

# --- Acquire OIDC token ---
if ! TOKEN="$(acquire_oidc_token)"; then
    logger -t "lm-prolog" "Could not acquire OIDC token for job ${JOB_ID}; rejecting"
    exit 1
fi

# --- Fetch the licenses tracked by License Manager for this cluster ---
# Only licenses configured in the API can be booked. Requesting an untracked
# license returns a 404 from the booking endpoint, which would otherwise reject
# the job. Filtering here lets jobs proceed when they mix tracked licenses with
# resources License Manager does not manage.
if ! http_request GET "${LM_API_BASE_URL}/lm/configurations/by_client_id" \
    -H "Authorization: Bearer ${TOKEN}" || [[ "$HTTP_CODE" -ne 200 ]]; then
    logger -t "lm-prolog" "Could not fetch tracked configurations for job ${JOB_ID} (HTTP ${HTTP_CODE}); rejecting"
    exit 1
fi

# Extract the set of tracked "product.feature" identifiers from the configurations.
TRACKED_PRODUCT_FEATURES="$(
    printf '%s' "$HTTP_BODY" \
        | grep -oE '"name":"[^"]+","product":\{"id":[0-9]+,"name":"[^"]+"' \
        | sed -E 's/"name":"([^"]+)","product":\{"id":[0-9]+,"name":"([^"]+)"/\2.\1/' || true
)"

# --- Build bookings for tracked licenses only ---
BOOKINGS=""
BOOKED_LICENSES=""
for i in "${!REQUESTED_PRODUCT_FEATURES[@]}"; do
    product_feature="${REQUESTED_PRODUCT_FEATURES[$i]}"
    if grep -qxF "$product_feature" <<< "$TRACKED_PRODUCT_FEATURES"; then
        [[ -n "$BOOKINGS" ]] && BOOKINGS+=","
        BOOKINGS+="{\"product_feature\":\"${product_feature}\",\"quantity\":${REQUESTED_QUANTITIES[$i]}}"
        [[ -n "$BOOKED_LICENSES" ]] && BOOKED_LICENSES+=","
        BOOKED_LICENSES+="${REQUESTED_LICENSES[$i]}"
    else
        logger -t "lm-prolog" "License ${REQUESTED_LICENSES[$i]} requested by job ${JOB_ID} is not tracked by License Manager; skipping"
    fi
done

# Exit if none of the requested licenses are tracked
if [[ -z "$BOOKINGS" ]]; then
    exit 0
fi

# --- Resolve lead host ---
LEAD_HOST="$("${SCONTROL_PATH:-/usr/bin/scontrol}" show hostnames "$JOB_NODELIST" | head -1)"
if [[ -z "$LEAD_HOST" ]]; then
    logger -t "lm-prolog" "Could not resolve lead host for job ${JOB_ID}; rejecting"
    exit 1
fi

# --- Make booking request ---
PAYLOAD="{\"slurm_job_id\":\"${JOB_ID}\",\"username\":\"${JOB_USER}\",\"lead_host\":\"${LEAD_HOST}\",\"bookings\":[${BOOKINGS}]}"

if http_request POST "${LM_API_BASE_URL}/lm/jobs" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$PAYLOAD" && [[ "$HTTP_CODE" -eq 201 ]]; then
    logger -t "lm-prolog" "Booking acquired for job ${JOB_ID} from user ${JOB_USER}, booked licenses: ${BOOKED_LICENSES}"
    exit 0
fi

logger -t "lm-prolog" "Booking request for job ${JOB_ID} failed with ${HTTP_CODE}: ${HTTP_BODY}"
exit 1
