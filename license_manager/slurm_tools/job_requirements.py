#!/bin/python3
"""slurm_job_requirements.py."""
import re
import subprocess
import sys

from license_manager.config import slurm_cmd
from license_manager.logging import log


# TODO: For a jobpack the license requirement may be stated
# in either of the jobs. Currently only the first job is considered.


def required_licenses_for_job(slurm_job_id, debug=False):
    """Retrieve the required licenses for a job."""
    cmd = [slurm_cmd.SCONTROL, "show", f"job={slurm_job_id}"]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = proc.communicate()
    std_out = std_out.decode("utf-8")

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(f"Could not get SLURM data for job id: {slurm_job_id}")
        return False

    # Check for requested licenses
    m = re.search(".* Licenses=([^ ]*).*", std_out)
    license_array = m.group(1).split(",")

    if license_array[0] == "(null)":
        return False
    else:
        licenses_requested = []
        for requested_license in license_array:

            # If license is given on the form feature@server
            if "@" in requested_license and ":" not in requested_license:
                # Request on format "feature@licserver"
                feature, license_server = requested_license.split("@")
                tokens = 1
            elif "@" in requested_license and ":" in requested_license:
                # Request on format "feature@licserver:no_tokens"
                feature, license_server, tokens = re.split(
                    "(\W+)", requested_license  # NOQA
                )[::2]
            elif requested_license and ":" in requested_license:
                # Request on format "feature:no_tokens"
                feature, tokens = requested_license.split(":")
                license_server = None
            elif requested_license and ":" not in requested_license:
                # Request on format "feature"
                feature = requested_license
                license_server = None
                tokens = 1
            else:
                log.error(f"Unsupported license request: {requested_license}")
                sys.exit(1)

            licenses_requested.append([feature, license_server, tokens])

        if debug:
            log.debug(f"License features requested by job id: {slurm_job_id}")
            for feature, license_server, tokens in licenses_requested:
                log.debug(
                    f"Feature: {feature}, "
                    f"Server: {license_server}, "
                    f"Tokens: {tokens}"
                )
        return licenses_requested


if __name__ == "__main__":
    job_id = sys.argv[1]
    requirements = required_licenses_for_job(job_id, debug=True)
    print(requirements)
