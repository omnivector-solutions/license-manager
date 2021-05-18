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
from licensemanager2.agent.backend_utils import get_license_server_features
from licensemanager2.agent import log, init_logging
from licensemanager2.workload_managers.slurm.common import get_job_context
from licensemanager2.workload_managers.slurm.cmd_utils import (
    LicenseBookingRequest,
    _force_reconciliation,
    _check_feature_token_availablity,
    _make_booking_request,
    get_required_licenses_for_job
)


async def main():
    """The PrologSlurmctld for the license-manager-agent."""
    # Acqure the job context
    job_id = get_job_context()["job_id"]

    license_booking_request = await get_required_licenses_for_job(job_id)

    # Create a list of tracked licenses in the form <product>.<feature>
    tracked_licenses = list()
    for license in get_license_server_features():
        for feature in license["features"]:
            tracked_licenses.append(f"{license['product']}.{feature}")

    # Create a tracked LicenseBookingRequest for licenses that we actually
    # track. These tracked licenses are what we will check feature token
    # availability for.
    tracked_license_booking_request = LicenseBookingRequest(
        job_id=job_id, bookings=[]
    )
    for license_booking in license_booking_request.bookings:
        if license_booking.product_feature in tracked_licenses:
            tracked_license_booking_request.bookings.append(license_booking)

    if len(tracked_license_booking_request.bookings) > 0:
        # Force a reconciliation before we check the feature tokenavailability.
        await _force_reconciliation()
        # Check that there are sufficient feature tokens for the job.
        feature_token_availability = _check_feature_token_availablity(
            tracked_license_booking_request
        )
        if feature_token_availability:
            # If we have sufficient tokens for features that are
            # requested, proceed with booking the tokens for each feature.
            booking_request = await _make_booking_request(
                tracked_license_booking_request
            )
            if booking_request:
                log.debug(f"License booking sucessful, job id: {job_id}.")
                log.debug(f"Licenses booked: {repr(tracked_licenses)}")
            else:
                log.debug("Booking request unsuccessful.")
                sys.exit(1)
        else:
            log.debug("Not enough feature tokens for job to proceed.")
            sys.exit(1)

    sys.exit(0)


# Initialize the logger
init_logging("slurmctld-prolog")
# Run main()
asyncio.run(main())