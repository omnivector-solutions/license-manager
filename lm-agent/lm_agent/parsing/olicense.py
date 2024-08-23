"""
Parser for OLicense
"""
import re
from typing import Optional
from lm_agent.models import LicenseUsesItem


HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
INT = r"\d+"
EXPIRATION_DATE = (
    r"[0-9]{4}-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9]"
)

FEATURE_LINE = (
    r"^\s+(?P<feature>\w+);"
    r"\s+(?P<license_type>\w+);"
    rf"\s+(?P<total>{INT});"
    rf"\s+(?P<expiration_date>{EXPIRATION_DATE});"
)

IN_USE_LINE = rf"^\s+(?P<in_use>{INT})\s+FloatsLockedBy"

USAGE_LINE = rf"^\s+(?P<user>\S+)@(?P<lead_host>{HOSTNAME})\s+#(?P<booked>{INT})$"

RX_FEATURE = re.compile(FEATURE_LINE)
RX_IN_USE = re.compile(IN_USE_LINE)
RX_USAGE = re.compile(USAGE_LINE)


def parse_feature_line(line: str) -> Optional[dict]:
    """
    Parse the "feature" line in the OLicense output.
    Data we need:
    - ``feature``: license name
    - ``total``: total amount of licenses

    Obs: OLicense supports more than one license with the same feature name.
    In case a feature has more than one license associated with it,
    the total amount of licenses is the sum of all licenses with the same name.
    """
    parsed_feature = RX_FEATURE.match(line)
    if parsed_feature is None:
        return None
    feature_data = parsed_feature.groupdict()

    return {
        "feature": feature_data["feature"].lower(),
        "total": int(feature_data["total"]),
    }


def parse_in_use_line(line: str) -> Optional[int]:
    """
    Parse the "in use" line in the Olicense output.
    Data we need:
    - ``in_use``: quantity of licenses being used by each user

    Obs: this line doesn't include the license name.
    The license in use is the last one parsed before this line.
    It also doesn't include the user name.
    The user using the license is the next "usage" line parsed after this line.
    The total amount of licenses being used is the sum of all "in use" lines.
    """

    parsed_in_use = RX_IN_USE.match(line)
    if parsed_in_use is None:
        return None
    in_use_data = parsed_in_use.groupdict()

    return int(in_use_data["in_use"])


def parse_usage_line(line: str) -> Optional[LicenseUsesItem]:
    """
    Parse the usage line in the Olicense output.
    Data we need:
    -``username``: user who booked the license
    -``lead_host``: host using the license
    -``booked``: quantity of licenses booked by the user

    Obs: this line also doesn't include the license name.
    The license in use is the last one parsed before this line.
    """
    parsed_usage = RX_USAGE.match(line)
    if parsed_usage is None:
        return None
    usage_data = parsed_usage.groupdict()

    return LicenseUsesItem(
        username=usage_data["user"].lower(),
        lead_host=usage_data["lead_host"],
        booked=int(usage_data["booked"]),
    )


def parse(server_output: str) -> dict:
    """
    Parse the OLicense output using regex to match the lines we need:
    -``feature line``: info about each license
    -``in use line``: info about licenses in use
    -``usage line``: info about users using licenses

    Since the "in use" and "usage" lines don't have the name of the license in use,
    we're saving each parsed license in a list. This way, we can find which
    license is being used by checking the last parsed license in the list.

    If a feature has more than one license associated with it, the total amount
    of licenses is the sum of all licenses with the same name.

    Example of output:
        ...
        ftire_adams;         	FreeFloating;	3;	2022-12-31 23:59:59;
        1 FloatsLockedBy:
        sbhyma@RD0087712 #1
        ...
        ftire_adams;         	FreeFloating;	1;	2023-02-28 23:59:00;

    This would be parsed as:
        "ftire_adams": {"total": 4, "used" 1, "uses": {
            "user_name": "sbhyma", "lead_host": "RD0087712", "booked": 1
        }}
    """
    parsed_data: dict = {}
    feature_list: list = []

    for line in server_output.splitlines():
        parsed_feature = parse_feature_line(line)
        if parsed_feature:
            feature = parsed_feature["feature"]
            total = parsed_feature["total"]
            if feature not in feature_list:
                feature_list.append(feature)
                parsed_data[feature] = {"used": 0, "total": total, "uses": []}
            else:
                parsed_data[feature]["total"] += total
            continue

        parsed_in_use = parse_in_use_line(line)
        if parsed_in_use:
            feature = feature_list[-1]
            parsed_data[feature]["used"] += parsed_in_use
            continue

        parsed_usage = parse_usage_line(line)
        if parsed_usage:
            feature = feature_list[-1]
            parsed_data[feature]["uses"].append(parsed_usage)

    return parsed_data
