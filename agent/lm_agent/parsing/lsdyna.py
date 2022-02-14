"""
Parser for LS-Dyna
"""

import re

HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
NONWS = r"\S+"
INT = r"\d+"
PROGRAM = r"[A-Z0-9\-_]+"
EXPIRATION_DATE = r"((0[1-9]|1[012])[\/](0[1-9]|[12][0-9]|3[01])[\/](19|20)\d\d)"
CPUS_USED = r"[\d|-]"

PROGRAM_LINE = (
    rf"(?P<program>{PROGRAM})\s+"
    rf"(?P<expiration_date>{EXPIRATION_DATE})\s+"
    rf"(?P<used>{CPUS_USED})\s+ "
    rf"(?P<free>{INT})\s+ "
    rf"(?P<max>{INT})\s+\|\s+"
    rf"(?P<queue>{INT})"
)

USAGE_LINE = (
    rf"\s+" rf"(?P<user>\S+)\s+" rf"(?P<port>{INT})\@" rf"(?P<lead_host>{HOSTNAME})\s+" rf"(?P<used>{INT})"
)

GROUP_LINE = (
    rf"\s+LICENSE GROUP\s+"
    rf"(?P<used>{INT})\s+"
    rf"(?P<free>{INT})\s+"
    rf"(?P<max>{INT})\s\|\s+"
    rf"(?P<queue>{INT})"
)

RX_PROGRAM = re.compile(PROGRAM_LINE)
RX_USAGE = re.compile(USAGE_LINE)
RX_TOTAL = re.compile(GROUP_LINE)


def parse(s: str) -> dict:
    """
    Parse lines of the license output with regular expressions
    """
    parsed_data: dict = {}
    group_used: int = 0

    lines = s.splitlines()

    for i, line in enumerate(lines):
        parsed_program = RX_PROGRAM.match(line)
        if parsed_program is None:
            continue
        program_data = parsed_program.groupdict()

        program_data["program"] = program_data["program"].lower()

        parsed_data[program_data["program"]] = {
            "total": int(program_data["max"]),
            "uses": [],
        }

        if program_data["used"] == "-":
            for line in lines[i + 1 :]:  # noqa: E203
                parsed_usage = RX_USAGE.match(line)
                if parsed_usage is None:
                    continue
                usage_data = parsed_usage.groupdict()
                parsed_data[program_data["program"]]["uses"].append(
                    {
                        "user_name": usage_data["user"],
                        "lead_host": usage_data["lead_host"],
                        "booked": int(usage_data["used"]),
                    }
                )

        parsed_total_usage = RX_TOTAL.match(line)
        if parsed_total_usage is None:
            continue

        total_usage_data = parsed_total_usage.groupdict()
        group_used = int(total_usage_data["used"])

    for program in parsed_data.keys():
        parsed_data[program]["used"] = group_used

    return parsed_data
