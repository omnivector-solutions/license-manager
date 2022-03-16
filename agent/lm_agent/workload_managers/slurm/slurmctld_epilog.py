#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.
"""
import asyncio
import sys

from lm_agent.backend_utils import backend_client
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import update_report
from lm_agent.workload_managers.slurm.cmd_utils import get_required_licenses_for_job
from lm_agent.workload_managers.slurm.common import get_job_context


async def _remove_booking_for_job(job_id: str) -> bool:
    """Remove token bookings used by job."""

    # Remove the booking for the job.
    resp = await backend_client.delete(f"lm/api/v1/booking/book/{job_id}")
    # Return True if the request to delete the booking was successful.
    if resp.status_code == 200:
        return True
    return False


async def epilog():
    # Initialize the logger
    init_logging("slurmctld-epilog")
    job_context = get_job_context()
    job_id = job_context["job_id"]
    job_licenses = job_context["job_licenses"]

    # Check if reconciliation should be triggered.
    if settings.USE_RECONCILE_IN_PROLOG_EPILOG:
        # Force a reconciliation before we attempt to remove bookings.
        try:
            await update_report()
        except Exception as e:
            logger.error(f"Failed to call reconcile with {e}")
            sys.exit(1)

    try:
        required_licenses = get_required_licenses_for_job(job_licenses)
    except Exception as e:
        logger.error(f"Failed to call get_required_licenses_for_job with {e}")
        sys.exit(1)

    if not required_licenses:
        logger.debug("No licenses required, exiting!")
        sys.exit(0)

    if len(required_licenses) > 0:
        # Attempt to remove the booking and log the result.
        booking_removed = await _remove_booking_for_job(job_id)
        if booking_removed:
            logger.debug(f"Booking for job id: {job_id} successfully deleted.")
        else:
            logger.debug(f"Booking for job id: {job_id} not removed.")


def main():
    asyncio.run(epilog())


if __name__ == "__main__":
    main()
