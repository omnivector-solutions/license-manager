#!/usr/bin/env python3
"""license_manager.server.slurm_tools.slurm_job_status"""
import subprocess

from license_manager.config import config
from license_manager.logging import log


def is_job_running(slurm_job_id):
    """Return a bool representing whether or not the job is running."""
    # Use squeue to check status of job
    cmd = [
        config.SQUEUE_PATH,
        '-j',
        slurm_job_id
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = proc.communicate()

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            f"Could not get SLURM data for job_id {slurm_job_id} - "
            f"{proc.returncode}"
        )
        return False

    # Read result, first line is header line, second line has job status
    job_status_row = std_out.split("\n")[1]
    job_status = job_status_row.split()[4]
    if job_status == 'R':
        return True
    else:
        return False


def job_state(slurm_job_id):
    """Get the job state."""
    # Use squeue to check status of job
    cmd = [
        config.SQUEUE_PATH,
        '-j',
        slurm_job_id
    ]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = proc.communicate()

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            "Could not get SLURM data for job_id {slurm_job_id} - "
            f"{proc.returncode}"
        )
        return False

    # Read result, first line is header line, second line has job status
    job_status_row = std_out.split("\n")[1]
    job_status = job_status_row.split()[4]
    return job_status
