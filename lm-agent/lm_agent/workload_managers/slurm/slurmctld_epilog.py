#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.
"""
import asyncio
import sys

from lm_agent.backend_utils.utils import remove_job_by_slurm_job_id
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.services.reconciliation import reconcile
from lm_agent.workload_managers.slurm.cmd_utils import get_required_licenses_for_job
from lm_agent.workload_managers.slurm.common import get_job_context


async def epilog():
    # Initialize the logger
    init_logging("slurmctld-epilog")
    job_context = await get_job_context()
    job_id = job_context["job_id"]
    job_licenses = job_context["job_licenses"]

    # Check if reconciliation should be triggered.
    if settings.USE_RECONCILE_IN_PROLOG_EPILOG:
        # Force a reconciliation before we attempt to remove bookings.
        try:
            await reconcile()
        except Exception as e:
            logger.critical(f"Failed to call reconcile with {e}")
            sys.exit(1)

    try:
        required_licenses = get_required_licenses_for_job(job_licenses)
    except Exception as e:
        logger.critical(f"Failed to call get_required_licenses_for_job with {e}")
        sys.exit(1)

    if not required_licenses:
        logger.debug(f"No licenses required for job {job_id}, exiting!")
        sys.exit(0)

    if len(required_licenses) > 0:
        # Attempt to remove the job with its bookings.
        await remove_job_by_slurm_job_id(job_id)
        logger.debug(f"Job {job_id} removed successfully")


def main():
    asyncio.run(epilog())


if __name__ == "__main__":
    main()
