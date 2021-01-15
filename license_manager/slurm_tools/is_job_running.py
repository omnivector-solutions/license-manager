#!/bin/python3
"""is_job_running"""
import re
import subprocess

from license_manager.config import slurm_cmd
from license_manager.logging import log


def is_slurm_job_running(job_id, slurm_controller, debug=False):
    """Determine whether or not a job is running."""
    cmd = [
        slurm_cmd.SACCT,
        "-j",
        str(job_id),
        "--parsable2",
        "--noheader",
        "-o",
        "State",
        "--allocations",
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    std_out, std_err = proc.communicate()

    # Decode output
    std_out = std_out.decode("utf-8")
    std_err = std_err.decode("utf-8")

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            f"Could not check status of job id: {job_id}. "
            f"stdout: {std_out}, stderr: {std_err}"
        )
        return False

    m = re.search(".*RUNNING.*", std_out)
    if m:
        if debug:
            log.debug(f"Status RUNNING - Job id: {job_id}")
        return True
    else:
        if debug:
            log.debug(f"Job not running - Job id: {job_id} - {std_out}")
        return False
