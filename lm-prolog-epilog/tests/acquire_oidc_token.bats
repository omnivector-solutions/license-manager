#!/usr/bin/env bats
# Tests for OIDC token acquisition and caching.

load test_helper

setup() {
    setup_common
    export OIDC_DOMAIN="auth.example/realms/test"
    export OIDC_CLIENT_ID="client"
    export OIDC_CLIENT_SECRET="secret"
    export OIDC_USE_HTTPS="false"
}

teardown() {
    teardown_common
}

@test "acquire_oidc_token reuses a valid cached token without calling curl" {
    mkdir -p "${LM_CACHE_DIR}"
    make_jwt "$(( $(date +%s) + 3600 ))" > "${LM_CACHE_DIR}/access.token"
    # curl stub fails loudly so a network call would break the test.
    install_stub curl 'echo "curl should not be called" >&2; exit 1'

    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; acquire_oidc_token'
    [ "$status" -eq 0 ]
    [ "$output" = "$(cat "${LM_CACHE_DIR}/access.token")" ]
}

@test "acquire_oidc_token fetches and caches a new token when cache is expired" {
    mkdir -p "${LM_CACHE_DIR}"
    make_jwt "$(( $(date +%s) - 100 ))" > "${LM_CACHE_DIR}/access.token"
    install_stub curl 'out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; printf "%s" "{\"access_token\":\"fresh-token\"}" > "$out"; printf "200"'

    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; acquire_oidc_token'
    [ "$status" -eq 0 ]
    [ "$output" = "fresh-token" ]
    [ "$(cat "${LM_CACHE_DIR}/access.token")" = "fresh-token" ]
}

@test "acquire_oidc_token caches the token with 0600 permissions" {
    install_stub curl 'out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; printf "%s" "{\"access_token\":\"t\"}" > "$out"; printf "200"'

    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; acquire_oidc_token'
    [ "$status" -eq 0 ]
    perms="$(stat -c '%a' "${LM_CACHE_DIR}/access.token" 2>/dev/null || stat -f '%Lp' "${LM_CACHE_DIR}/access.token")"
    [ "$perms" = "600" ]
}

@test "acquire_oidc_token fails when the provider returns non-200" {
    install_stub curl 'out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; printf "%s" "{\"error\":\"nope\"}" > "$out"; printf "401"'

    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; acquire_oidc_token'
    [ "$status" -ne 0 ]
}

@test "acquire_oidc_token fails when the response has no access_token" {
    install_stub curl 'out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; printf "%s" "{\"expires_in\":300}" > "$out"; printf "200"'

    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; acquire_oidc_token'
    [ "$status" -ne 0 ]
}
