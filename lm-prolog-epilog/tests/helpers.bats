#!/usr/bin/env bats
# Unit tests for the shared helper functions in acquire_oidc_token.sh.

load test_helper

setup() {
    setup_common
    source "${REPO_DIR}/acquire_oidc_token.sh"
}

teardown() {
    teardown_common
}

@test "json_value extracts a string field" {
    run json_value '{"access_token":"abc123","token_type":"Bearer"}' access_token
    [ "$status" -eq 0 ]
    [ "$output" = "abc123" ]
}

@test "json_value tolerates surrounding whitespace" {
    run json_value '{ "access_token" :  "spaced" }' access_token
    [ "$output" = "spaced" ]
}

@test "json_value returns empty for a missing key" {
    run json_value '{"a":"b"}' missing
    [ "$output" = "" ]
}

@test "json_number extracts a numeric field" {
    run json_number '{"exp":1700000000,"iat":1699990000}' exp
    [ "$output" = "1700000000" ]
}

@test "http_request returns body and code on success" {
    install_stub curl 'out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; printf "%s" "{\"ok\":true}" > "$out"; printf "200"'
    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; http_request GET http://x/ && echo "$HTTP_CODE $HTTP_BODY"'
    [ "$status" -eq 0 ]
    [ "$output" = "200 {\"ok\":true}" ]
}

@test "http_request does not retry on a 4xx response" {
    install_stub curl 'echo x >> "'"${TMP_DIR}"'/calls"; out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; : > "$out"; printf "400"'
    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; http_request GET http://x/; echo "$HTTP_CODE"'
    [ "$output" = "400" ]
    [ "$(wc -l < "${TMP_DIR}/calls")" -eq 1 ]
}

@test "http_request retries on 5xx then succeeds" {
    install_stub curl '
n=$(cat "'"${TMP_DIR}"'/n" 2>/dev/null || echo 0); n=$((n+1)); echo "$n" > "'"${TMP_DIR}"'/n"
out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; : > "$out"
if [ "$n" -lt 3 ]; then printf "503"; else printf "201"; fi'
    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; http_request POST http://x/ 2>/dev/null; echo "$HTTP_CODE"'
    [ "$output" = "201" ]
    [ "$(cat "${TMP_DIR}/n")" -eq 3 ]
}

@test "http_request gives up after MAX_ATTEMPTS on persistent 5xx" {
    install_stub curl 'echo x >> "'"${TMP_DIR}"'/calls"; out=""; prev=""; for a in "$@"; do [ "$prev" = "-o" ] && out="$a"; prev="$a"; done; : > "$out"; printf "503"'
    run bash -c 'source "'"${REPO_DIR}"'/acquire_oidc_token.sh"; http_request GET http://x/ 2>/dev/null; echo "rc=$? code=$HTTP_CODE"'
    [ "$output" = "rc=1 code=503" ]
    [ "$(wc -l < "${TMP_DIR}/calls")" -eq 3 ]
}
