"""Utilities that interact with slurm."""
import re
from typing import Dict, List, Optional, Union

from lm_agent.exceptions import ScontrolRetrievalFailure, SqueueParserUnexpectedInputError
from lm_agent.models import LicenseBooking
from lm_agent.logs import logger, log_error
from lm_agent.config import settings
from lm_agent.utils import run_command


def _match_requested_license(requested_license: str) -> Union[dict, None]:
    license_regex = re.compile(
        r"(?P<product>[a-zA-Z0-9-_]+)\.(?P<feature>[a-zA-Z0-9-_]+)@(?P<server_type>\w+)(:(?P<tokens>\d+))?"
    )

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
        booked = matched_license_items["tokens"]

        # Create the license booking
        license_booking = LicenseBooking(
            product_feature=product_feature,
            quantity=booked,
        )
        required_licenses.append(license_booking)

    return required_licenses


async def get_all_features_cluster_values() -> Optional[Dict[str, Dict[str, int]]]:
    """
    Parse the output from `scontrol show lic` and return a dictionary of
    product_feature: {"total": <total>, "used": <used>}.

    Note: the line with the counters doesn't include the feature name,
    so to find the feature it's necessary to look at the previous line.
    """
    product_feature_line = re.compile(
        r"LicenseName=(?P<product>[a-zA-Z0-9-_]+).(?P<feature>[a-zA-Z0-9-_]+)@(?P<license_server_type>\w+)"
    )

    used_tokens_line = re.compile(
        r"^\s*Total=(?P<total>\d+) Used=(?P<used>\d+) Free=(?P<free>\d+) Reserved=(?P<reserved>\d+) Remote=(?P<remote>\w+)"  # noqa
    )

    scontrol_output = await scontrol_show_lic()

    parsed_data: dict = {}
    product_feature_list: list = []

    for line in scontrol_output.split("\n"):
        parsed_product_feature = product_feature_line.match(line)
        if parsed_product_feature:
            product_feature_data = parsed_product_feature.groupdict()
            product_feature = product_feature_data["product"] + "." + product_feature_data["feature"]
            product_feature_list.append(product_feature)
            continue

        parsed_used_tokens = used_tokens_line.match(line)
        if parsed_used_tokens:
            used_data = parsed_used_tokens.groupdict()
            product_feature = product_feature_list[-1]
            parsed_data[product_feature] = {"total": int(used_data["total"]), "used": int(used_data["used"])}
            continue

    return parsed_data


async def scontrol_show_lic():
    """
    Get the license usage from scontrol.
    """

    cmd = [
        str(settings.SCONTROL_PATH),
        "show",
        "lic",
    ]
    output = await run_command(cmd)

    logger.debug("##### scontrol show lic #####")
    return output


async def get_lead_host(nodelist):
    """
    Get the job's lead host from the nodelist.

    The lead host is the first node in the nodelist.
    The nodelist can contain multiple lists of nodes inside square brackets.
    """
    cmd = [
        str(settings.SCONTROL_PATH),
        "show",
        "hostnames",
        nodelist,
    ]
    output = await run_command(cmd)

    lead_host = output.split("\n")[0]
    ScontrolRetrievalFailure.require_condition(lead_host != "", "Could not get lead host from nodelist")

    return lead_host


async def get_all_product_features_from_cluster() -> List[str]:
    """
    Returns a list of all product.feature in the cluster.
    """
    show_lic_output = await scontrol_show_lic()

    PRODUCT_FEATURE = r"LicenseName=(?P<product>[a-zA-Z0-9-_]+).(?P<feature>[a-zA-Z0-9-_]+)"
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


async def return_formatted_squeue_out() -> str:
    """
    Call squeue via Popen and return the formatted output.

    Return the squeue output in the form "<job_id>|<run_time>|<state>".
    """
    cmd = [
        str(settings.SQUEUE_PATH),
        "--noheader",
        "--format='%A|%M|%T'",
    ]

    return await run_command(cmd)


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
        with SqueueParserUnexpectedInputError.handle_errors(
            "Unexpected input from squeue", do_except=log_error
        ):
            job_id, run_time, state = line.strip("'").split("|")

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
