#!/usr/bin/env bats
# End-to-end tests for slurmctld_epilog.sh with stubbed curl/logger.

load test_helper

EPILOG_REL="slurmctld_epilog.sh"

setup() {
    setup_common
    install_e2e_curl
    export LM_CONFIG_FILE="$(write_config)"
    export SLURM_JOB_ID="42"
}

teardown() {
    teardown_common
}

@test "epilog releases bookings and exits 0 on 200" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export BOOKING_CODE=200
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
    grep -q "/lm/jobs/slurm_job_id/42" "${CURL_ARGS_FILE}"
}

@test "epilog treats 404 as success and exits 0" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export BOOKING_CODE=404
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
}

@test "epilog exits 0 even when the delete keeps failing with 5xx" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export BOOKING_CODE=500
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
}

@test "epilog exits 0 and makes no request without tracked licenses" {
    export SLURM_JOB_LICENSES="gpu:2"
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
    [ ! -f "${CURL_ARGS_FILE}" ]
}

@test "epilog does not delete when requested licenses are not tracked" {
    export TRACKED_CONFIGS_JSON="$(tracked_configs_json abaqus.abaqus)"
    export SLURM_JOB_LICENSES="unknown.unknown@flexlm:1"
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
    ! grep -q "/lm/jobs/slurm_job_id/42" "${CURL_ARGS_FILE}"
}

@test "epilog exits 0 when the OIDC token cannot be acquired" {
    export SLURM_JOB_LICENSES="abaqus.abaqus@flexlm:1"
    export TOKEN_CODE=401
    run bash "${REPO_DIR}/${EPILOG_REL}"
    [ "$status" -eq 0 ]
    # The delete endpoint must never be called without a token.
    ! grep -q "/lm/jobs/slurm_job_id/42" "${CURL_ARGS_FILE}"
}
