#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.

This epilog is responsible for releasing the feature tokens
that have been booked for a job back to the pool after a job has completed.
"""
import asyncio
import sys

import httpx

from lm_agent.backend_utils import get_config_from_backend
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.workload_managers.slurm.cmd_utils import (
    get_required_licenses_for_job,
    get_tokens_for_license,
    sacctmgr_modify_resource,
)
from lm_agent.workload_managers.slurm.common import LM2_AGENT_HEADERS, get_job_context


async def _remove_booking_for_job(job_id: str) -> bool:
    """Remove token bookings used by job."""

    # Remove the booking for the job.

    with httpx.Client() as client:
        resp = client.delete(
            f"{settings.AGENT_BASE_URL}/api/v1/booking/book/{job_id}",
            headers=LM2_AGENT_HEADERS,
        )

        # Return True if the request to delete the booking was successful.
        if resp.status_code == 200:
            return True
    return False


async def main():
    # Initialize the logger
    init_logging("slurmctld-epilog")

    # Acqure the job context and get the job_id.
    ctxt = get_job_context()
    job_id = ctxt["job_id"]
    user_name = ctxt["user_name"]
    lead_host = ctxt["lead_host"]

    try:
        license_booking_request = await get_required_licenses_for_job(job_id, user_name, lead_host)
    except Exception as e:
        logger.error(f"Failed to call get_required_licenses_for_job with {e}")
        sys.exit(1)

    if len(license_booking_request.bookings) > 0:
        # Create a list of tracked licenses in the form <product>.<feature>
        tracked_licenses = list()
        try:
            entries = await get_config_from_backend()
        except Exception as e:
            logger.error(f"Failed to call get_config_from_backend with {e}")
            sys.exit(1)
        for entry in entries:
            for feature in entry.features:
                tracked_licenses.append(f"{entry.product}.{feature}")

        # If a license booking's product feature is tracked,
        # update slurm's view of the token totals
        for license_booking in license_booking_request.bookings:
            product_feature = license_booking.product_feature
            product, feature = product_feature.split(".")
            license_server_type = license_booking.license_server_type
            tokens_to_remove = license_booking.tokens
            license = f"{product_feature}@{license_server_type}"

            if product_feature in tracked_licenses:
                try:
                    total = await get_tokens_for_license(license, "Total")
                except Exception as e:
                    logger.error(f"Failed to call get_tokens_for_license with {e}")
                    sys.exit(1)
                update_resource = await sacctmgr_modify_resource(product, feature, total - tokens_to_remove)

                if update_resource:
                    logger.info("Slurmdbd updated successfully.")
                else:
                    logger.info("Slurmdbd update unsuccessful.")

        # Attempt to remove the booking and log the result.
        booking_removed = await _remove_booking_for_job(job_id)
        if booking_removed:
            logger.debug(f"Booking for job id: {job_id} successfully deleted.")
        else:
            logger.debug(f"Booking for job id: {job_id} not removed.")
    sys.exit(0)


if __name__ == "__main__":
    # Run main()
    asyncio.run(main())
