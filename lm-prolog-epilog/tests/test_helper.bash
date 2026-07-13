#!/usr/bin/env bash
# Shared setup for the License Manager prolog/epilog bats tests.
#
# Sourced from each *.bats file. Provides a temp working dir, a stub-binary
# directory placed first on PATH, and helpers to install stubs.

setup_common() {
    REPO_DIR="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
    export REPO_DIR

    TMP_DIR="$(mktemp -d)"
    export TMP_DIR

    # Directory for stub executables (curl, scontrol, logger, ...).
    STUB_BIN="${TMP_DIR}/bin"
    mkdir -p "${STUB_BIN}"
    export STUB_BIN
    export PATH="${STUB_BIN}:${PATH}"

    # Keep the token cache and any writes inside the temp dir.
    export LM_CACHE_DIR="${TMP_DIR}/cache"

    # Make retries fast during tests.
    export LM_MAX_ATTEMPTS=3
    export LM_RETRY_DELAY=0

    # logger is not guaranteed to be meaningful in CI; stub it as a no-op.
    install_stub logger 'exit 0'
}

teardown_common() {
    rm -rf "${TMP_DIR}"
}

# install_stub NAME BODY
# Create an executable stub called NAME in STUB_BIN running BODY.
install_stub() {
    local name="$1" body="$2"
    cat >"${STUB_BIN}/${name}" <<EOF
#!/usr/bin/env bash
${body}
EOF
    chmod +x "${STUB_BIN}/${name}"
}

# install_scontrol - stub scontrol so it resolves a single lead host.
install_scontrol() {
    cat >"${STUB_BIN}/scontrol" <<'STUB'
#!/usr/bin/env bash
echo "node01"
STUB
    chmod +x "${STUB_BIN}/scontrol"
}

# install_e2e_curl - stub curl for end-to-end prolog/epilog tests.
# It answers the OIDC token endpoint with ${TOKEN_CODE:-200} plus a token
# body, and any other endpoint with ${BOOKING_CODE:-201}. Every invocation's
# arguments are appended (one per line) to ${CURL_ARGS_FILE}.
install_e2e_curl() {
    export CURL_ARGS_FILE="${TMP_DIR}/curl_args"
    cat >"${STUB_BIN}/curl" <<'STUB'
#!/usr/bin/env bash
out=""; prev=""; url=""
for a in "$@"; do
  [ "$prev" = "-o" ] && out="$a"
  case "$a" in http://*|https://*) url="$a";; esac
  prev="$a"
done
printf '%s\n' "$@" >> "$CURL_ARGS_FILE"
if [[ "$url" == *openid-connect/token* ]]; then
  [ -n "$out" ] && printf '%s' '{"access_token":"header.payload.sig"}' > "$out"
  printf '%s' "${TOKEN_CODE:-200}"
  exit 0
fi
[ -n "$out" ] && : > "$out"
printf '%s' "${BOOKING_CODE:-201}"
exit 0
STUB
    chmod +x "${STUB_BIN}/curl"
}

# Write a minimal config file and echo its path.
write_config() {
    local cfg="${TMP_DIR}/license-manager-agent"
    cat >"${cfg}" <<EOF
LM_API_BASE_URL="http://api.example"
OIDC_DOMAIN="auth.example/realms/test"
OIDC_CLIENT_ID="client"
OIDC_CLIENT_SECRET="secret"
OIDC_USE_HTTPS="false"
SCONTROL_PATH="${STUB_BIN}/scontrol"
EOF
    echo "${cfg}"
}

# Build a JWT-like token whose payload decodes to {"exp": EXP}.
make_jwt() {
    local exp="$1" payload
    payload="$(printf '{"exp":%s}' "${exp}" | base64 | tr -d '=\n')"
    printf 'header.%s.signature' "${payload}"
}
