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

import httpx

from licensemanager2.agent.settings import SETTINGS
from licensemanager2.agent import log, init_logging
from licensemanager2.workload_managers.slurm.common import (
    LM2_AGENT_HEADERS,
    SCONTROL_PATH,
    SCONTROL_TIMEOUT,
    get_job_context
)


async def _get_required_licenses_for_job(slurm_job_id: str) -> dict:
    """Retrieve the required licenses for a job."""

    # Initialize the dict to hold license information for the job.
    license_request_for_job = {"job_id": slurm_job_id, "licenses": dict()}

    # Command to get license information back from slurm using the
    # slurm_job_id.
    cmd = [
        SCONTROL_PATH,
        "show",
        f"job={slurm_job_id}"
    ]

    scontrol_show_lic = await asyncio.create_subprocess_shell(
        join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    scontrol_out, _ = await asyncio.wait_for(
        scontrol_show_lic.communicate(),
        SCONTROL_TIMEOUT
    )
    scontrol_out = str(scontrol_out, encoding="UTF8")
    log.info(scontrol_out)

    # Check that the command completed successfully
    if not scontrol_show_lic.returncode == 0:
        log.error(f"Could not get SLURM data for job id: {slurm_job_id}")
        raise Exception(f"Could not get SLURM data for job id: {slurm_job_id}")

    # Parse license information from scontrol output
    m = re.search('.* Licenses=([^ ]*).*', scontrol_out)
    license_array = m.group(1).split(',')

    if license_array[0] != "(null)":
        for requested_license in license_array:

            # If license is given on the form feature@server
            if '@' in requested_license and ':' not in requested_license:
                # Request on format "feature@licserver"
                feature, license_server = requested_license.split('@')
                tokens = 1
            elif '@' in requested_license and ':' in requested_license:
                feature, license_server_tokens = requested_license.split("@")
                license_server, tokens = requested_license.split(":")
            elif requested_license and ':' in requested_license:
                # Request on format "feature:no_tokens"
                feature, tokens = requested_license.split(':')
                license_server = None
            elif requested_license and ':' not in requested_license:
                # Request on format "feature"
                feature = requested_license
                license_server = None
                tokens = 1
            else:
                log.error(f"Unsupported license request: {requested_license}")
                sys.exit(1)

            license_request_for_job["licenses"][feature] = {
                "license_server": license_server,
                "tokens": tokens
            }

        log.debug(f"License features requested by job id: {slurm_job_id}")
        for product_feature in license_request_for_job["licenses"].keys():
            feature_tokens = license_request_for_job[
                "licenses"][product_feature]["tokens"]
            lic_server = license_request_for_job[
                "licenses"][product_feature]["license_server"]

            log.debug(
                f"Feature: {product_feature}, "
                f"Server: {lic_server}, "
                f"Tokens: {feature_tokens}"
            )
    return license_request_for_job


async def _check_feature_token_availablity(booking_request: dict) -> bool:
    """Determine if there are sufficient tokens to fill the request."""

    # Set all feature availability to false initially
    feature_availability = {
        feature: False
        for feature in booking_request["licenses"].keys()
    }

    # We currently only have an "/all" endpoint.
    # Todo: Implement endpoint to retrieve counts for a
    # specific feature so we dont have to get them all.
    with httpx.Client() as client:
        resp = client.get(
            f"{SETTINGS.AGENT_BASE_URL}/api/v1/license/all",
            headers=LM2_AGENT_HEADERS
        )

        for item in resp.json():
            product_feature = item["product_feature"]
            if product_feature in feature_availability.keys():
                tokens_requested = int(
                    booking_request['licenses'][product_feature]["tokens"]
                )
                tokens_available = int(item["available"])
                if tokens_available >= tokens_requested:
                    feature_availability[product_feature] = True

    # Check that the license-manager backend is tracking the features
    # we request.
    if all(feature_availability.values()):
        return True
    return False


async def _make_booking_request(booking_request: dict) -> bool:
    """Book feature tokens."""

    feature_tokens = list()
    # Prepare data for request
    for feature in booking_request["licenses"].keys():
        tokens = booking_request["licenses"][feature]["tokens"]
        feature_tokens.append({"product_feature": feature, "booked": tokens})

    data = {
        "job_id": booking_request["job_id"],
        "features": feature_tokens
    }

    with httpx.Client() as client:
        resp = client.put(
            f"{SETTINGS.AGENT_BASE_URL}/api/v1/booking/book",
            headers=LM2_AGENT_HEADERS,
            json=data
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
    # Acqure the job context
    ctxt = get_job_context()
    log.info(ctxt)
    job_id = ctxt["job_id"]
    booking_request = await _get_required_licenses_for_job(job_id)
    licenses = booking_request["licenses"]

    # Check if any licenses required for the job.
    if len(licenses) > 0:
        if not await _force_reconciliation():
            sys.exit(1)
        # Check that there are sufficient feature tokens for the job.
        if await _check_feature_token_availablity(booking_request):
            # If we have sufficient tokens for each feature then
            # proceed with booking the tokens for each feature.
            if await _make_booking_request(booking_request):
                log.debug(f"License booking succeeded for job id: {job_id}.")
                log.debug(f"Licenses booked: {repr(licenses)}")
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
