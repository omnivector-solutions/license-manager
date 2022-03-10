"""
Parser for LM-X
"""
import re
from typing import Optional

HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
INT = r"\d+"
VERSION = rf"{INT}\.{INT}"

FEATURE_LINE = rf"^Feature: (?P<feature>\w+) Version: (?P<version>{VERSION}) Vendor: (?P<vendor>\S+)$"
IN_USE_LINE = rf"^(?P<in_use>{INT}) of (?P<total>{INT}) license\(s\) used(:)?$"
USAGE_LINE = (
    rf"^(?P<in_use>{INT}) license\(s\) "
    rf"used by (?P<user>\S+)@(?P<lead_host>{HOSTNAME}) "
    rf"\[{INT}\.{INT}\.{INT}\.{INT}\]"
)
RX_FEATURE = re.compile(FEATURE_LINE)
RX_IN_USE = re.compile(IN_USE_LINE)
RX_USAGE = re.compile(USAGE_LINE)


def parse_feature_line(line: str) -> Optional[str]:
    """
    Parse the feature line in the LM-X output.
    Data we need:
    - ``feature``: license name
    """
    parsed_feature = RX_FEATURE.match(line)
    if parsed_feature is None:
        return None
    feature_data = parsed_feature.groupdict()

    return feature_data["feature"].lower()


def parse_in_use_line(line: str) -> Optional[dict]:
    """
    Parse the in use line in the LM-X output.
    Data we need:
    - ``in_use``: quantity of licenses being use
    - ``total``: total amount of licenses

    Obs: this line doesn't include the license name.
    The license in use is the last one parsed before this line.
    """

    parsed_in_use = RX_IN_USE.match(line)
    if parsed_in_use is None:
        return None
    in_use_data = parsed_in_use.groupdict()

    return {
        "used": int(in_use_data["in_use"]),
        "total": int(in_use_data["total"]),
    }


def parse_usage_line(line: str) -> Optional[dict]:
    """
    Parse the usage line in the LS-Dyna output.
    Data we need:
    -``user_name``: user who booked the license
    -``lead_host``: host using the license
    -``booked``: quantity of licenses being used

    Obs: this line also doesn't incluse the license name.
    The license in use is the last one parsed before this line.
    """
    parsed_usage = RX_USAGE.match(line)
    if parsed_usage is None:
        return None
    usage_data = parsed_usage.groupdict()

    return {
        "user_name": usage_data["user"],
        "lead_host": usage_data["lead_host"],
        "booked": int(usage_data["in_use"]),
    }


def parse(server_output: str) -> dict:
    """
    Parse the LM-X output using regex to match the lines we need:
    -``feature line``: info about each license
    -``in use line``: info about licenses in use
    -``usage line``: info about users using licenses

    Since the in use and usage line don't have the name of the license in use,
    we're saving each parsed license in a list. This way, we can find which
    license is being used by checking the last parsed license in the list.
    """
    parsed_data: dict = {}
    feature_list: list = []

    for line in server_output.splitlines():
        parsed_feature = parse_feature_line(line)
        parsed_in_use = parse_in_use_line(line)
        parsed_usage = parse_usage_line(line)

        if parsed_feature:
            parsed_data[parsed_feature] = {}
            feature_list.append(parsed_feature)

        elif parsed_in_use:
            feature = feature_list[-1]
            parsed_data[feature] = {
                "used": parsed_in_use["used"],
                "total": parsed_in_use["total"],
                "uses": [],
            }
        elif parsed_usage:
            feature = feature_list[-1]
            parsed_data[feature]["uses"].append(parsed_usage)
        else:
            continue

    return parsed_data
