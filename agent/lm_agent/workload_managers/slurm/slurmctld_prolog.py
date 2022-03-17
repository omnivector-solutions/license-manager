#!/usr/bin/env python3
"""
The SlurmctldProlog executable.

This prolog is responsible for checking if feature tokens are available
and making booking requests by communicating with the license-manager agent
(which should be running on the slurmctld host).

Executing this script will result in either an exit(0) or exit(1). Slurm will
proceed with scheduling the job if the exit status is 0, and will not proceed
if the exit status is anything other then 0, e.g. 1.
"""
import asyncio
import sys

from lm_agent.backend_utils import get_config_from_backend
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import update_report
from lm_agent.workload_managers.slurm.cmd_utils import (
    LicenseBookingRequest,
    get_required_licenses_for_job,
    make_booking_request,
)
from lm_agent.workload_managers.slurm.common import get_job_context


async def prolog():
    """The PrologSlurmctld for the license-manager-agent."""
    # Initialize the logger
    init_logging("slurmctld-prolog")
    # Acqure the job context
    job_context = get_job_context()
    job_id = job_context.get("job_id", "")
    user_name = job_context.get("user_name")
    lead_host = job_context.get("lead_host")
    cluster_name = job_context.get("cluster_name")
    job_licenses = job_context.get("job_licenses")

    logger.info(f"Prolog started for job id: {job_id}")

    try:
        required_licenses = get_required_licenses_for_job(job_licenses)
        logger.debug(f"Required licenses: {required_licenses}")
    except Exception as e:
        logger.error(f"Failed to call get_required_licenses_for_job with {e}")
        sys.exit(1)

    if not required_licenses:
        logger.debug("No licenses required, exiting!")
        sys.exit(0)

    tracked_licenses = list()
    # Create a list of tracked licenses in the form <product>.<feature>

    if len(required_licenses) > 0:
        # Create a list of tracked licenses in the form <product>.<feature>
        try:
            entries = await get_config_from_backend()
        except Exception as e:
            logger.error(f"Failed to call get_config_from_backend with {e}")
            sys.exit(1)
        for entry in entries:
            for feature in entry.features:
                tracked_licenses.append(f"{entry.product}.{feature}")
    logger.debug(f"Tracked licenses: {tracked_licenses}")

    # Create a tracked LicenseBookingRequest for licenses that we actually
    # track. These tracked licenses are what we will check feature token
    # availability for.
    tracked_license_booking_request = LicenseBookingRequest(
        job_id=job_id,
        bookings=[],
        user_name=user_name,
        lead_host=lead_host,
        cluster_name=cluster_name,
    )
    for booking in required_licenses:
        if booking.product_feature in tracked_licenses:
            tracked_license_booking_request.bookings.append(booking)
    logger.debug(f"Tracked license bookings: {tracked_license_booking_request}")

    if len(tracked_license_booking_request.bookings) > 0:
        # Check if reconciliation should be triggered.
        if settings.USE_RECONCILE_IN_PROLOG_EPILOG:
            # Force a reconciliation before we check the feature token availability.
            try:
                await update_report()
            except Exception as e:
                logger.error(f"Failed to call reconcile with {e}")
                sys.exit(1)

        booking_request = await make_booking_request(tracked_license_booking_request)
        if not booking_request:
            logger.debug("Booking request unsuccessful, not enough licenses.")
            sys.exit(1)
        logger.debug(f"License booking sucessful, job id: {job_id}.")
        logger.debug(f"Licenses booked: {repr(tracked_license_booking_request.bookings)}")
    sys.exit(0)


def main():
    asyncio.run(prolog())


if __name__ == "__main__":
    main()
