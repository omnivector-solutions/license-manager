"""Utilities that interact with slurm."""
import asyncio
import re
import shlex
import subprocess
from typing import List, Optional, Union

import httpx
from pydantic import BaseModel, Field

from lm_agent.config import PRODUCT_FEATURE_RX, settings
from lm_agent.logs import logger
from lm_agent.workload_managers.slurm.common import (
    CMD_TIMEOUT,
    ENCODING,
    LM2_AGENT_HEADERS,
    SACCTMGR_PATH,
    SCONTROL_PATH,
    SQUEUE_PATH,
)


class SqueueParserUnexpectedInputError(ValueError):
    """Unexpected squeue output."""


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
    user_name: str
    lead_host: str


def _match_requested_license(requested_license: str) -> Union[dict, None]:
    license_regex = re.compile(r"(?P<product>\w+)\.(?P<feature>\w+)@(?P<server_type>\w+):(?P<tokens>\d+)")
    matches = license_regex.match(requested_license)

    if not matches:
        return None
    groups = matches.groupdict()
    return {
        "product_feature": groups["product"] + "." + groups["feature"],
        "server_type": groups["server_type"],
        "tokens": int(groups["tokens"]),
    }


async def get_required_licenses_for_job(
    slurm_job_id: str, user_name: str, lead_host: str
) -> Union[LicenseBookingRequest, None]:
    """Retrieve the required licenses for a job."""

    license_array = await get_licenses_for_job(slurm_job_id)
    logger.debug(f"##### License array for job id: {slurm_job_id} #####")
    logger.debug(license_array)

    license_booking_request = LicenseBookingRequest(
        job_id=slurm_job_id,
        bookings=[],
        user_name=user_name,
        lead_host=lead_host,
    )
    if not license_array:
        return None

    if license_array[0] == "(null)":
        return None

    for requested_license in license_array:
        matched_license_items = _match_requested_license(requested_license)
        if not matched_license_items:
            continue
        product_feature = matched_license_items["product_feature"]
        license_server_type = matched_license_items["server_type"]
        tokens = matched_license_items["tokens"]
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

    logger.info(f"##### Checking feature token availability for: {lbr.job_id} #####")

    # We currently only have an "/all" endpoint.
    # Todo: Implement endpoint to retrieve counts for a
    # specific feature, or set of features so that we dont have to get /all.
    with httpx.Client() as client:
        resp = client.get(f"{settings.AGENT_BASE_URL}/api/v1/license/all", headers=LM2_AGENT_HEADERS)
        logger.debug("##### /api/v1/license/all #####")
        data = resp.json()
        logger.debug(f"response data: {data}")
        logger.debug(f"lbr: {lbr}")

        for item in data:
            product_feature = item["product_feature"]
            for license_booking in lbr.bookings:
                if product_feature == license_booking.product_feature:
                    tokens_available = int(item["available"])
                    if tokens_available >= license_booking.tokens:
                        logger.debug(f"##### {product_feature}, tokens avalable #####")
                        logger.debug(f"##### Tokens available {tokens_available} #####")
                        logger.debug(f"##### Tokens required {license_booking.tokens} #####")
                        return True
                    else:
                        logger.debug(f"##### {product_feature}, tokens not available #####")
                        logger.debug(f"##### Tokens available {tokens_available} #####")
                        logger.debug(f"##### Tokens required {license_booking.tokens} #####")
    logger.debug("##### Tokens not available #####")
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

    logger.debug(f"features: {features}")
    logger.debug(f"lbr: {lbr}")

    with httpx.Client() as client:
        resp = client.put(
            f"{settings.AGENT_BASE_URL}/api/v1/booking/book",
            headers=LM2_AGENT_HEADERS,
            json={
                "job_id": lbr.job_id,
                "features": features,
                "user_name": lbr.user_name,
                "lead_host": lbr.lead_host,
            },
        )

    if resp.status_code == 200:
        logger.debug("##### Booking completed successfully #####")
        return True
    logger.debug(f"##### Booking failed: {resp.status_code} #####")
    return False


async def reconcile():
    """Force a reconciliation."""

    with httpx.Client() as client:
        resp = client.get(
            f"{settings.AGENT_BASE_URL}/reconcile",
            headers=LM2_AGENT_HEADERS,
        )

    if resp.status_code == 200:
        logger.debug("##### Reconcile completed successfully #####")
        return True
    logger.debug(f"##### Reconcile failed {resp.status_code} #####")
    return False


async def get_licenses_for_job(slurm_job_id: str) -> List:
    """
    Parse the scontrol output and return licenses needed for job.
    """

    # Command to get license information back from slurm using the
    # slurm_job_id.
    scontrol_show_lic = await asyncio.create_subprocess_shell(
        shlex.join([SCONTROL_PATH, "show", f"job={slurm_job_id}"]),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    scontrol_out_bytes, _ = await asyncio.wait_for(scontrol_show_lic.communicate(), CMD_TIMEOUT)
    scontrol_out = scontrol_out_bytes.decode(ENCODING)
    logger.debug("##### scontrol out #####")
    logger.debug(scontrol_out)

    # Check that the command completed successfully
    if not scontrol_show_lic.returncode == 0:
        msg = f"Could not get SLURM data for job id: {slurm_job_id}"
        logger.error(msg)
        raise ScontrolRetrievalFailure(msg)

    # Parse license information from scontrol output
    m = re.search(".* Licenses=([^ ]*).*", scontrol_out)
    if not m:
        msg = f"Command output for {slurm_job_id=} was malformed: no 'Licenses' section found"
        logger.error(msg)
        raise ScontrolRetrievalFailure(msg)

    match_string = m.group(1)
    if match_string == "(null)":
        return []

    license_list = match_string.split(",")
    return license_list


async def get_tokens_for_license(
    product_feature_server: str,
    output_type: str,
) -> Optional[int]:
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
        shlex.join(cmd), stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )

    stdout, _ = await asyncio.wait_for(proc.communicate(), CMD_TIMEOUT)
    output = str(stdout, encoding=ENCODING)
    logger.debug("##### scontrol show lic #####")
    logger.debug(output)
    return output


async def sacctmgr_modify_resource(product: str, feature: str, num_tokens) -> bool:
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
    logger.debug("##### sacctmgr update cmd #####")
    logger.debug(f"{' '.join(cmd)}")

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


def return_formatted_squeue_out() -> str:
    """
    Call squeue via Popen and return the formatted output.

    Return the squeue output in the form "<job_id>|<run_time>|<state>".
    """

    result = subprocess.run(
        f"{shlex.quote(SQUEUE_PATH)} --noheader --format='%A|%M|%T'",
        capture_output=True,
        shell=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        logger.error(result.stderr)
        raise Exception(result.stderr)

    return result.stdout.strip()


def _total_time_in_seconds(time_string: str) -> int:
    """
    Return the runtime in seconds for a job.

    This function takes a slurm time string ("<days>-<hours>:<minutes>:<seconds>") as input, parses
    and converts each of the units in the time string to seconds and returns a computed value, the sum of
    the days, hours, minutes and seconds (in seconds).
    """
    MINUTE = 60
    HOUR = 60 * MINUTE
    DAY = 24 * HOUR

    days = 0
    hours = 0
    splitted_time = [int(value) for value in re.split("-|:", time_string)]
    splitted_time_len = len(splitted_time)

    if splitted_time_len == 4:
        days, hours, minutes, seconds = splitted_time
    elif splitted_time_len == 3:
        hours, minutes, seconds = splitted_time
    else:
        minutes, seconds = splitted_time

    return days * DAY + hours * HOUR + minutes * MINUTE + seconds


def squeue_parser(squeue_formatted_output) -> List:
    """Parse the squeue formatted output."""

    squeue_parsed_output: List = []

    if not squeue_formatted_output:
        return squeue_parsed_output

    def parse_squeue_line():
        """Parse a line from squeue formatted output."""
        try:
            job_id, run_time, state = line.split("|")
        except ValueError as e:
            logger.error(e)
            raise SqueueParserUnexpectedInputError()
        return job_id, run_time, state

    for line in squeue_formatted_output.split():
        job_id, run_time, state = parse_squeue_line()
        squeue_parsed_output.append(
            {
                "job_id": int(job_id),
                "run_time_in_seconds": _total_time_in_seconds(run_time),
                "state": state,
            }
        )

    return squeue_parsed_output
