"""Utilities that interact with slurm."""
import asyncio
import httpx
import re
import shlex

from pydantic import BaseModel, Field
from licensemanager2.workload_managers.slurm.common import (
    CMD_TIMEOUT,
    SCONTROL_PATH,
    SACCTMGR_PATH,
    ENCODING,
    LM2_AGENT_HEADERS,
)
from licensemanager2.agent import log as logger
from typing import List, Optional, Union
from licensemanager2.agent.settings import (
    SETTINGS,
    PRODUCT_FEATURE_RX,
)


class ScontrolRetrievalFailure(Exception):
    """
    Could not get SLURM data for job id.
    The following function's return code was zero:

    await asyncio.create_subprocess_shell(
        shlex.join([SCONTROL_PATH, "show", f"job={slurm_job_id}"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    """
    pass


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


async def get_required_licenses_for_job(slurm_job_id: str) -> LicenseBookingRequest:
    """Retrieve the required licenses for a job."""

    license_array = await get_licenses_for_job(slurm_job_id)
    license_booking_request = LicenseBookingRequest(
        job_id=slurm_job_id,
        bookings=[],
    )

    if license_array[0] != "(null)":
        for requested_license in license_array:
            license_regex = re.compile(r'(\w+)\.(\w+)@(\w+):(\d+)')
            if license_regex.match(requested_license):
                # If the regex matches, parse the values
                product_feature, license_server_tokens = \
                    requested_license.split("@")
                license_server_type, tokens = requested_license.split(":")

                # Create the license booking
                license_booking = LicenseBooking(
                    product_feature=product_feature,
                    tokens=tokens,
                    license_server_type=license_server_type,
                )

                license_booking_request.bookings.append(license_booking)

    return license_booking_request


async def check_feature_token_availablity(lbr: LicenseBookingRequest) -> bool:
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


async def make_booking_request(lbr: LicenseBookingRequest) -> bool:
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


async def reconcile():
    """Force a reconciliation."""

    with httpx.Client() as client:
        resp = client.get(
            f"{SETTINGS.AGENT_BASE_URL}/reconcile",
            headers=LM2_AGENT_HEADERS,
        )

    if resp.status_code == 200:
        return True
    return False


async def get_licenses_for_job(slurm_job_id: str) -> List:
    """
    Parse the scontrol output and return licenses needed for job.

    Note: "type: ignore" was used to silence mypy type errors

    See github issue: https://github.com/omnivector-solutions/license-manager/issues/19
    """

    # Command to get license information back from slurm using the
    # slurm_job_id.
    scontrol_show_lic = await asyncio.create_subprocess_shell(
        shlex.join([SCONTROL_PATH, "show", f"job={slurm_job_id}"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    scontrol_out, _ = await asyncio.wait_for(
        scontrol_show_lic.communicate(),
        CMD_TIMEOUT
    )
    scontrol_out = str(scontrol_out, ENCODING)  # type: ignore
    logger.info(scontrol_out)

    # Check that the command completed successfully
    if not scontrol_show_lic.returncode == 0:
        msg = f"Could not get SLURM data for job id: {slurm_job_id}"
        logger.error(msg)
        raise ScontrolRetrievalFailure(msg)

    # Parse license information from scontrol output
    m = re.search('.* Licenses=([^ ]*).*', scontrol_out)  # type: ignore
    license_list = m.group(1).split(',')  # type: ignore
    return license_list


async def get_tokens_for_license(
        product_feature_server: str,
        output_type: str) -> Optional[int]:
    """
    Return tokens from scontrol output.
    """

    def match_product_feature_server() -> Optional[str]:
        """
        Return the line after the matched product_feature line.
        """
        matched = False
        for line in scontrol_output.split("\n"):
            if matched:
                return line
            if len(re.findall(rf"({product_feature_server})", line)) > 0:
                matched = True
        return None

    # Get the scontrol output
    scontrol_output = await scontrol_show_lic()

    # Match the product_feature_server
    token_str = match_product_feature_server()
    if token_str is not None:
        for item in token_str.split():
            k, v = item.split("=")
            if k == output_type:
                return int(v)
    return None


async def scontrol_show_lic():
    """
    Get the license usage from scontrol.
    """

    cmd = [
        SCONTROL_PATH,
        "show",
        "lic",
    ]

    proc = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT
    )

    stdout, _ = await asyncio.wait_for(proc.communicate(), CMD_TIMEOUT)
    output = str(stdout, encoding=ENCODING)
    return output


async def sacctmgr_modify_resource(
        product: str, feature: str, num_tokens) -> bool:
    """
    Update the license resource in slurm.
    """
    cmd = [
        SACCTMGR_PATH,
        "modify",
        "resource",
        f"name={product}.{feature}",
        "set",
        f"count={num_tokens}",
        "-i",
    ]
    logger.info(f"{' '.join(cmd)}")

    sacctmgr_modify_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    modify_resource_stdout, _ = await asyncio.wait_for(
        sacctmgr_modify_resource.communicate(),
        CMD_TIMEOUT,
    )

    rc = sacctmgr_modify_resource.returncode

    if not rc == 0:
        logger.warning(f"rc = {rc}!")
        logger.warning(modify_resource_stdout)
        return False
    return True
