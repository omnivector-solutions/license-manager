"""
Parser for RLM
"""
import re
from typing import Optional
from lm_agent.models import LicenseUsesItem


INT = r"\d+"
VERSION = rf"v{INT}\.{INT}"
HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTWORD2 = r"[a-zA-Z0-9-.]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD2})*"
FEATURE_NAME = r"[\w-]+"

FEATURE_LINE = rf"^\s*(?P<license_feature>{FEATURE_NAME}) {VERSION}$"
COUNT_LINE = r"^\s*count: (?P<count>\d+).*inuse: (?P<in_use>\d+).*$"
USAGE_LINE = rf"^\s*(?P<license_feature>{FEATURE_NAME}) {VERSION}: (?P<user_name>\w+)@(?P<lead_host>{HOSTNAME}) (?P<license_used_by_host>\d+).*$"  # noqa

RX_FEATURE = re.compile(FEATURE_LINE)
RX_COUNT = re.compile(COUNT_LINE)
RX_USAGE = re.compile(USAGE_LINE)


def parse_feature_line(line: str) -> Optional[str]:
    """
    Parse the feature line in the RLM output.
    Data we need:
    - ``feature``: license name
    """
    parsed_feature = RX_FEATURE.match(line)
    if parsed_feature is None:
        return None
    feature_data = parsed_feature.groupdict()
    if feature_data["license_feature"] == "rlmutil":
        return None

    return feature_data["license_feature"].lower()


def parse_count_line(line: str) -> Optional[dict]:
    """
    Parse the count line in the RLM output.
    Data we need:
    - ``count``: total amount of licenses
    - ``in_use``: quantity of licenses being use
    """
    parsed_count = RX_COUNT.match(line)
    if parsed_count is None:
        return None
    count_data = parsed_count.groupdict()

    return {
        "count": int(count_data["count"]),
        "in_use": int(count_data["in_use"]),
    }


def parse_usage_line(line: str) -> Optional[dict]:
    """
    Parse the usage line in the RLM output.
    Data we need:
    - ``feature``: license name
    - ``username``: user name
    - ``lead_host``: lead host
    - ``license_used_by_host``: quantity of licenses being use
    """
    parsed_usage = RX_USAGE.match(line)
    if parsed_usage is None:
        return None
    usage_data = parsed_usage.groupdict()

    return {
        "license_feature": usage_data["license_feature"].lower(),
        "use": LicenseUsesItem(
            username=usage_data["user_name"].lower(),
            lead_host=usage_data["lead_host"],
            booked=int(usage_data["license_used_by_host"]),
        ),
    }


def parse(server_output: str) -> dict:
    """
    Parse the output from the RLM server.
    Data we need:
    - ``feature``: license name
    - ``count``: total amount of licenses
    - ``in_use``: quantity of licenses being use
    """
    parsed_data: dict = {}
    feature_list: list = []

    for line in server_output.splitlines():
        feature = parse_feature_line(line)
        if feature:
            feature_list.append(feature)
            parsed_data[feature] = {"uses": [], "total": []}
            continue

        count = parse_count_line(line)
        if count:
            feature = feature_list[-1]
            parsed_data[feature] = {
                "used": count["in_use"],
                "total": count["count"],
                "uses": [],
            }
            continue

        usage = parse_usage_line(line)
        if usage:
            feature = usage["license_feature"]
            del usage["license_feature"]
            parsed_data[feature]["uses"].append(usage["use"])
            continue

        else:
            continue

    return parsed_data
