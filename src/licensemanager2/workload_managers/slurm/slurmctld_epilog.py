#!/usr/bin/env python3
"""The SlurmctldEpilog executable.

This epilog is responsible for releasing the feature tokens
that have been booked for a job back to the pool after a job has completed.
"""
import requests

from licensemanager2.workload_managers.slurm.settings import SETTINGS
from licensemanager2.workload_managers.slurm.command_logger import (
    log,
    init_logging,
)
from licensemanager2.workload_managers.slurm.common import (
    LM2_AGENT_HEADERS,
    get_job_context
)


def _remove_booking_for_job(job_id: str) -> bool:
    """Remove token bookings used by job."""

    # Remove the booking for the job.
    resp = requests.delete(
        f"{SETTINGS.AGENT_BASE_URL}/api/v1/booking/book/{job_id}",
        headers=LM2_AGENT_HEADERS,
    )

    # Return True if the request to delete the booking was successful.
    if resp.status_code == 200:
        return True
    return False


def main():
    # Initialize the logger
    init_logging("slurmctld-epilog")

    # Acqure the job context and get the job_id.
    ctxt = get_job_context()
    job_id = ctxt["job_id"]

    # Attempt to remove the booking and log the result.
    booking_removed = _remove_booking_for_job(job_id)
    if booking_removed:
        log.debug(f"Booking for job id: {job_id} successfully deleted.")
    else:
        log.debug(f"Booking for job id: {job_id} not removed.")


if __name__ == "__main__":
    main()
