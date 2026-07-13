# shellcheck shell=bash
# acquire_oidc_token.sh - Shared helpers for the License Manager prolog/epilog.
#
# Provides OIDC token acquisition (with on-disk caching) and a small HTTP
# helper with retry/backoff. Meant to be sourced by the SlurmctldProlog an
# SlurmctldEpilog scripts; sourcing it has no side effects.

CACHE_DIR="${LM_CACHE_DIR:-/var/cache/license-manager}"
TOKEN_CACHE="${CACHE_DIR}/access.token"

# Retry behaviour for network calls.
MAX_ATTEMPTS="${LM_MAX_ATTEMPTS:-3}"
RETRY_DELAY="${LM_RETRY_DELAY:-2}"

# Extract a string value from a flat JSON object by key.
json_value() {
    local json="$1" key="$2"
    echo "$json" | grep -o "\"${key}\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" | sed "s/\"${key}\"[[:space:]]*:[[:space:]]*\"//;s/\"$//"
}

# Extract a numeric value from a flat JSON object by key.
json_number() {
    local json="$1" key="$2"
    echo "$json" | grep -o "\"${key}\"[[:space:]]*:[[:space:]]*[0-9]*" | grep -o '[0-9]*$'
}

# http_request METHOD URL [curl args...]
# Performs an HTTP request, retrying on connection errors and 5xx responses
# with exponential backoff. On return the response body is available in
# HTTP_BODY and the status code in HTTP_CODE. Returns 0 when a response with a
# status < 500 was received, non-zero otherwise.
http_request() {
    local method="$1" url="$2"
    shift 2

    local attempt=1 delay="$RETRY_DELAY" body_file
    body_file="$(mktemp)"

    while true; do
        HTTP_CODE="$(curl -sS -o "$body_file" -w '%{http_code}' \
            --connect-timeout 5 --max-time 30 \
            -X "$method" "$url" "$@" 2>/dev/null)" || HTTP_CODE="000"

        if [[ "$HTTP_CODE" != "000" && "$HTTP_CODE" -lt 500 ]]; then
            break
        fi

        if (( attempt >= MAX_ATTEMPTS )); then
            break
        fi

        logger -t "lm-http" "Request $method $url failed (attempt ${attempt}/${MAX_ATTEMPTS}, HTTP ${HTTP_CODE}); retrying in ${delay}s"
        sleep "$delay"
        delay=$(( delay * 2 ))
        (( attempt++ ))
    done

    HTTP_BODY="$(cat "$body_file")"
    rm -f "$body_file"

    [[ "$HTTP_CODE" != "000" && "$HTTP_CODE" -lt 500 ]]
}

# acquire_oidc_token - echo a valid OIDC access token, reusing the on-disk
# cache when possible. Returns non-zero on failure.
acquire_oidc_token() {
    # Try cached token
    if [[ -f "$TOKEN_CACHE" ]]; then
        local cached_token jwt_payload pad decoded exp now
        cached_token="$(cat "$TOKEN_CACHE")"
        # Decode JWT payload (second segment) and check expiry with a 30s buffer
        jwt_payload="$(echo "$cached_token" | cut -d. -f2)"
        pad=$(( ${#jwt_payload} % 4 ))
        if [[ "$pad" -eq 2 ]]; then jwt_payload+="=="; elif [[ "$pad" -eq 3 ]]; then jwt_payload+="="; fi
        decoded="$(echo "$jwt_payload" | base64 -d 2>/dev/null)" || decoded=""
        exp="$(json_number "$decoded" "exp")"
        now="$(date +%s)"
        if [[ -n "$exp" && "$exp" -gt "$(( now + 30 ))" ]]; then
            echo "$cached_token"
            return 0
        fi
    fi

    # Acquire a new token
    local protocol="https"
    if [[ "${OIDC_USE_HTTPS:-true}" == "false" ]]; then
        protocol="http"
    fi
    local oidc_url="${protocol}://${OIDC_DOMAIN}/protocol/openid-connect/token"

    if ! http_request POST "$oidc_url" \
        -d "client_id=${OIDC_CLIENT_ID}" \
        -d "client_secret=${OIDC_CLIENT_SECRET}" \
        -d "grant_type=client_credentials"; then
        logger -t "lm-auth" "Failed to reach OIDC provider at ${oidc_url}"
        return 1
    fi

    if [[ "$HTTP_CODE" -ne 200 ]]; then
        logger -t "lm-auth" "OIDC token request failed with HTTP ${HTTP_CODE}: $HTTP_BODY"
        return 1
    fi

    local token
    token="$(json_value "$HTTP_BODY" "access_token")"
    if [[ -z "$token" ]]; then
        logger -t "lm-auth" "OIDC response did not contain an access_token"
        return 1
    fi

    # Cache token with restrictive permissions
    mkdir -p "$CACHE_DIR"
    ( umask 077; echo -n "$token" > "$TOKEN_CACHE" )

    echo "$token"
}
