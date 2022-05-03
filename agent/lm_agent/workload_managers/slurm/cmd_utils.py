"""Utilities that interact with slurm."""
import asyncio
import re
import shlex
import subprocess
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from lm_agent.backend_utils import backend_client
from lm_agent.config import PRODUCT_FEATURE_RX
from lm_agent.logs import logger
from lm_agent.workload_managers.slurm.common import (
    CMD_TIMEOUT,
    ENCODING,
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
    cluster_name: str


def _match_requested_license(requested_license: str) -> Union[dict, None]:
    license_regex = re.compile(r"(?P<product>\w+)\.(?P<feature>\w+)@(?P<server_type>\w+)(:(?P<tokens>\d+))?")

    matches = license_regex.match(requested_license)

    if not matches:
        return None

    groups = matches.groupdict()
    if not groups["tokens"]:
        groups["tokens"] = "1"

    return {
        "product_feature": groups["product"] + "." + groups["feature"],
        "server_type": groups["server_type"],
        "tokens": int(groups["tokens"]),
    }


def get_required_licenses_for_job(job_licenses: str) -> List:
    """Retrieve the required licenses for a job."""

    license_array = job_licenses.split(",")
    logger.debug(f"##### License array for job: {license_array} #####")

    required_licenses: List = []

    if not license_array:
        return required_licenses

    if license_array[0] == "(null)":
        return required_licenses

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
        required_licenses.append(license_booking)

    return required_licenses


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

    resp = await backend_client.put(
        "/lm/api/v1/booking/book",
        json={
            "job_id": lbr.job_id,
            "features": features,
            "user_name": lbr.user_name,
            "lead_host": lbr.lead_host,
            "cluster_name": lbr.cluster_name,
        },
    )

    if resp.status_code == 200:
        logger.debug("##### Booking completed successfully #####")
        return True
    logger.debug(f"##### Booking failed: {str(resp.content)} #####")
    return False


async def reconcile():
    """Force a reconciliation."""
    resp = await backend_client.get("/lm/api/v1/license/reconcile")

    if resp.status_code == 200:
        logger.debug("##### Reconcile completed successfully #####")
        return True
    logger.debug(f"##### Reconcile failed {resp.status_code} #####")
    return False


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


async def get_cluster_name() -> str:
    cmd = [
        SACCTMGR_PATH,
        "list",
        "cluster",
        "-nP",
        "format=Cluster",
    ]
    logger.debug("##### sacctmgr get cluster name cmd #####")
    logger.debug(f"{' '.join(cmd)}")

    sacctmgr_modify_resource = await asyncio.create_subprocess_shell(
        shlex.join(cmd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    cluster_name_stdout, _ = await asyncio.wait_for(
        sacctmgr_modify_resource.communicate(),
        CMD_TIMEOUT,
    )
    return cluster_name_stdout.decode("utf8").strip()


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


async def get_all_product_features_from_cluster() -> List[str]:
    """
    Returns a list of all product.feature in the cluster.
    """
    show_lic_output = await scontrol_show_lic()

    PRODUCT_FEATURE = r"LicenseName=(?P<product>[a-zA-Z0-9_]+)[_\-.](?P<feature>\w+)"
    RX_PRODUCT_FEATURE = re.compile(PRODUCT_FEATURE)

    parsed_features = []
    output = show_lic_output.split("\n")
    for line in output:
        parsed_line = RX_PRODUCT_FEATURE.match(line)
        if parsed_line:
            parsed_data = parsed_line.groupdict()
            product = parsed_data["product"]
            feature = parsed_data["feature"]
            parsed_features.append(f"{product}.{feature}")

    return parsed_features


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
