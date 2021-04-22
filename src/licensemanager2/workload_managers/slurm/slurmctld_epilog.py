#!/usr/bin/env python3
"""The SlurmctldEpilog executable.
This epilog is responsible for releasing the feature tokens
that have been booked for a job back to the pool after a job has completed.
"""
import asyncio
import httpx

from licensemanager2.agent import log, init_logging
from licensemanager2.agent.settings import SETTINGS
from licensemanager2.workload_managers.slurm.common import (
    LM2_AGENT_HEADERS,
    get_job_context
)


async def _remove_booking_for_job(job_id: str) -> bool:
    """Remove token bookings used by job."""

    # Remove the booking for the job.

    with httpx.Client() as client:
        resp = client.delete(
            f"{SETTINGS.AGENT_BASE_URL}/api/v1/booking/book/{job_id}",
            headers=LM2_AGENT_HEADERS,
        )

        # Return True if the request to delete the booking was successful.
        if resp.status_code == 200:
            return True
    return False


async def main():
    # Acqure the job context and get the job_id.
    ctxt = get_job_context()
    job_id = ctxt["job_id"]

    # Attempt to remove the booking and log the result.
    booking_removed = await _remove_booking_for_job(job_id)
    if booking_removed:
        log.debug(f"Booking for job id: {job_id} successfully deleted.")
    else:
        log.debug(f"Booking for job id: {job_id} not removed.")


# Initialize the logger
init_logging("slurmctld-epilog")
# Run main()
asyncio.run(main())
