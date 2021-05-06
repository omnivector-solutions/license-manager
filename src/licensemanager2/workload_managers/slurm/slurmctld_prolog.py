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
import re
import sys

from shlex import join
from typing import Union, List

import httpx

from pydantic import BaseModel, Field

from licensemanager2.agent.settings import SETTINGS
from licensemanager2.agent.tokenstat import ENCODING, PRODUCT_FEATURE_RX
from licensemanager2.agent.backend_utils import get_license_server_features
from licensemanager2.agent import log, init_logging
from licensemanager2.workload_managers.slurm.common import (
    LM2_AGENT_HEADERS,
    SCONTROL_PATH,
    CMD_TIMEOUT,
    get_job_context
)


class LicenseBooking(BaseModel):
    """
    Structure to represent a license booking.
    """
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    tokens: int
    license_server_type: Union[None, str]


class LicenseBookingRequest(BaseModel):
    """
    Structure to represent a list of license bookings.
    """
    job_id: int
    bookings: Union[List, List[LicenseBooking]]


async def _get_required_licenses_for_job(slurm_job_id: str) -> LicenseBookingRequest:
    """Retrieve the required licenses for a job."""

    # Command to get license information back from slurm using the
    # slurm_job_id.
    scontrol_show_lic = await asyncio.create_subprocess_shell(
        join([SCONTROL_PATH, "show", f"job={slurm_job_id}"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    scontrol_out, _ = await asyncio.wait_for(
        scontrol_show_lic.communicate(),
        CMD_TIMEOUT
    )
    scontrol_out = str(scontrol_out, encoding=ENCODING)
    log.info(scontrol_out)

    # Check that the command completed successfully
    if not scontrol_show_lic.returncode == 0:
        msg = f"Could not get SLURM data for job id: {slurm_job_id}"
        log.error(msg)
        raise Exception(msg)

    # Parse license information from scontrol output
    m = re.search('.* Licenses=([^ ]*).*', scontrol_out)
    license_array = m.group(1).split(',')

    license_booking_request = LicenseBookingRequest(job_id=slurm_job_id, bookings=[])

    if license_array[0] != "(null)":
        for requested_license in license_array:

            # If license is given on the form feature@server
            if '@' in requested_license and ':' not in requested_license:
                # Request on format "feature@licserver"
                product_feature, license_server_type = requested_license.split('@')
                tokens = 1
            elif '@' in requested_license and ':' in requested_license:
                product_feature, license_server_tokens = requested_license.split("@")
                license_server_type, tokens = requested_license.split(":")
            elif requested_license and ':' in requested_license:
                # Request on format "feature:no_tokens"
                product_feature, tokens = requested_license.split(':')
                license_server_type = None
            elif requested_license and ':' not in requested_license:
                # Request on format "feature"
                product_feature = requested_license
                license_server_type = None
                tokens = 1
            else:
                log.error(f"Unsupported license request: {requested_license}")
                sys.exit(1)

                license_booking = LicenseBooking(
                    product_feature=product_feature,
                    tokens=tokens,
                    license_server_type=license_server_type,
                )

                license_booking_request.bookings.append(license_booking)

    return license_booking_request


async def _check_feature_token_availablity(lbr: LicenseBookingRequest) -> bool:
    """Determine if there are sufficient tokens to fill the request."""

    # We currently only have an "/all" endpoint.
    # Todo: Implement endpoint to retrieve counts for a
    # specific feature, or set of features so that we dont have to get /all.
    with httpx.Client() as client:
        resp = client.get(
            f"{SETTINGS.AGENT_BASE_URL}/api/v1/license/all",
            headers=LM2_AGENT_HEADERS
        )

        for item in resp.json():
            product_feature = item["product_feature"]
            for license_booking in lbr.bookings:
                if product_feature == license_booking.product_feature:
                    tokens_available = int(item["available"])
                    if tokens_available >= license_booking.tokens:
                        return True
    return False


async def _make_booking_request(lbr: LicenseBookingRequest) -> bool:
    """Book the feature tokens."""

    features = [
        {
            "product_feature": license_booking.product_feature,
            "booked": license_booking.tokens,
        }
        for license_booking in lbr.bookings
    ]

    with httpx.Client() as client:
        resp = client.put(
            f"{SETTINGS.AGENT_BASE_URL}/api/v1/booking/book",
            headers=LM2_AGENT_HEADERS,
            json={"job_id": lbr.job_id, "features": features}
        )

    if resp.status_code == 200:
        return True
    return False


async def _force_reconciliation():
    """Force a reconciliation."""

    with httpx.Client() as client:
        resp = client.get(
            f"{SETTINGS.AGENT_BASE_URL}/reconcile",
            headers=LM2_AGENT_HEADERS,
        )

    if resp.status_code == 200:
        return True
    return False


async def main():
    """The PrologSlurmctld for the license-manager-agent."""
    # Acqure the job context
    job_id = get_job_context()["job_id"]

    license_booking_request = await _get_required_licenses_for_job(job_id)

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
