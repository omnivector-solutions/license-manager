"""
Parser for FlexLM
"""
import re
from typing import Dict, Optional
from lm_agent.models import LicenseUsesItem


HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
NONWS = r"\S+"
NONCOLON = r"[^:]+"
INT = r"\d+"
NONPAREN = r"[^() ]+"
MMDD = rf"{INT}/{INT}"
HHMM = rf"{INT}:{INT}"
FEATURE_NAME = r"[A-Za-z0-9\-_:]+"


FEATURE_LINE = (
    r"^Users of "
    rf"(?P<feature>{FEATURE_NAME}):  "
    r"\(Total of "
    rf"(?P<total>{INT}) "
    r"licenses issued;  Total of "
    rf"(?P<used>{INT}) "
    rf"license(?P<plural>s)? in use\)$"
)

USAGE_LINE_1 = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{NONWS}) "
    rf"\((?P<version>{NONPAREN})\) "
    rf"\((?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})\), "
    r"start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM}), "
    rf"(?P<tokens>{INT}) "
    r"licenses$"
)

USAGE_LINE_2 = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{NONWS}) "
    r"feature="
    rf"(?P<feature>{FEATURE_NAME}) "
    rf"\(v(?P<version>{NONPAREN})\) "
    rf"\((?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})\), "
    r"start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM}), "
    rf"(?P<tokens>{INT}) "
    r"licenses$"
)


USAGE_LINE_3 = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{NONWS}) "
    rf"\(v(?P<version>{NONPAREN})\) "
    rf"\((?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})\), "
    r"start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM})$"
)

USAGE_LINE_4 = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{HOSTNAME}) "
    rf"(?P<feature>{FEATURE_NAME}) "
    rf"\(v(?P<version>{NONPAREN})\) "
    rf"\((?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})\), "
    r"start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM}), "
    rf"(?P<tokens>{INT}) "
    r"licenses$"
)

USAGE_LINE_5 = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{NONWS}) "
    rf"(?P<feature>{FEATURE_NAME}) "
    rf"\(v(?P<version>{NONPAREN})\) "
    rf"\((?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})\), "
    r"start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM})$"
)

RX_FEATURE = re.compile(FEATURE_LINE)
RX_USAGE_LINE_1 = re.compile(USAGE_LINE_1)
RX_USAGE_LINE_2 = re.compile(USAGE_LINE_2)
RX_USAGE_LINE_3 = re.compile(USAGE_LINE_3)
RX_USAGE_LINE_4 = re.compile(USAGE_LINE_4)
RX_USAGE_LINE_5 = re.compile(USAGE_LINE_5)
USAGE_LINES = [RX_USAGE_LINE_1, RX_USAGE_LINE_2, RX_USAGE_LINE_3, RX_USAGE_LINE_4, RX_USAGE_LINE_5]


def parse_feature_line(line: str) -> Optional[Dict]:
    """
    Parse the feature line in the FlexLM output.
    Data we need:
    - ``feature``: license name
    - ``total``: total amount of licenses
    - ``used``: quantity of licenses being used
    """
    parsed_feature = RX_FEATURE.match(line)
    if parsed_feature is None:
        return None
    feature_data = parsed_feature.groupdict()

    return {
        "feature": feature_data["feature"].lower(),
        "total": int(feature_data["total"]),
        "used": int(feature_data["used"]),
    }


def parse_usage_line(line: str) -> Optional[LicenseUsesItem]:
    """
    Parse the usage line in the FlexLM output.
    Data we need:
    - ``username``: user who booked the license
    - ``lead_host``: host using the license
    - ``booked``: quantity of licenses being used

    There can be multiple formats for the data line, so we need to check which one matches.
    """

    for RX in USAGE_LINES:
        if parsed_data := RX.match(line):
            break

    if parsed_data is None:
        return None

    data = parsed_data.groupdict()

    return LicenseUsesItem(
        username=data["user"].lower(),
        lead_host=data["user_host"],
        booked=int(data.get("tokens", 1)),
    )


def parse(server_output: str) -> Dict:
    """
    Parse the FlexLM Output, using regext to match the lines we need:
    - ``feature line``: info about the license
    - ``data line``: info about the users using the license
    """
    parsed_data: dict = {}
    uses = []

    for line in server_output.splitlines():
        parsed_feature = parse_feature_line(line)

        if parsed_feature:
            parsed_data = parsed_feature
            continue

        parsed_data_line = parse_usage_line(line)

        if parsed_data_line:
            uses.append(parsed_data_line)

    if parsed_data:
        parsed_data["uses"] = uses

    return parsed_data
