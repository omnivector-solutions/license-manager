#!/usr/bin/env bats
# End-to-end tests for slurmcltd_prolog.sh with stubbed curl/scontrol/logger.

load test_helper

PROLOG_REL="slurmctld_prolog.sh"

setup() {
    setup_common
    install_scontrol
    install_e2e_curl
    export LM_CONFIG_FILE="$(write_config)"
    export SLURM_JOB_ID="42"
    export SLURM_JOB_USER="alice"
    export SLURM_JOB_NODELIST="node[01-02]"
}

teardown() {
    teardown_common
}

@test "prolog books tracked licenses and exits 0" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:2"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
}

@test "prolog posts the expected booking payload" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:2,matlab.matlab@rlm"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
    grep -q '"slurm_job_id":"42"' "${CURL_ARGS_FILE}"
    grep -q '"username":"alice"' "${CURL_ARGS_FILE}"
    grep -q '"lead_host":"node01"' "${CURL_ARGS_FILE}"
    grep -q '{"product_feature":"abaqus.abaqus","quantity":2}' "${CURL_ARGS_FILE}"
    grep -q '{"product_feature":"matlab.matlab","quantity":1}' "${CURL_ARGS_FILE}"
    grep -q "${LM_API_BASE_URL:-http://api.example}/lm/jobs" "${CURL_ARGS_FILE}"
}

@test "prolog rejects the job (exit 1) when the API rejects the booking" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export BOOKING_CODE=409
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 1 ]
}

@test "prolog rejects the job (exit 1) when booking keeps failing with 5xx" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export BOOKING_CODE=503
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 1 ]
}

@test "prolog exits 0 and makes no request when no licenses are requested" {
    export SLURM_JOB_LICENSES=""
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
    [ ! -f "${CURL_ARGS_FILE}" ]
}

@test "prolog exits 0 when only untracked resources are requested" {
    export SLURM_JOB_LICENSES="gpu:2"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
    [ ! -f "${CURL_ARGS_FILE}" ]
}

@test "prolog books only tracked licenses and skips untracked ones" {
    export TRACKED_CONFIGS_JSON="$(tracked_configs_json abaqus.abaqus)"
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:2,unknown.unknown@flexlm:1"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
    grep -q '{"product_feature":"abaqus.abaqus","quantity":2}' "${CURL_ARGS_FILE}"
    ! grep -q 'unknown.unknown' "${CURL_ARGS_FILE}"
}

@test "prolog exits 0 without booking when all requested licenses are untracked" {
    export TRACKED_CONFIGS_JSON="$(tracked_configs_json abaqus.abaqus)"
    export SLURM_JOB_LICENSES="unknown.unknown@flexlm:1"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 0 ]
    ! grep -q "${LM_API_BASE_URL:-http://api.example}/lm/jobs" "${CURL_ARGS_FILE}"
}

@test "prolog rejects the job (exit 1) when tracked configurations cannot be fetched" {
    export TRACKED_CODE=503
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    run bash "${REPO_DIR}/${PROLOG_REL}"
    [ "$status" -eq 1 ]
}
