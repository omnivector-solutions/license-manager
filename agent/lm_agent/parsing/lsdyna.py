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
    rf"\s+" rf"(?P<user>\S+)\s+" rf"(?P<port>\d+)\@" rf"(?P<lead_host>{HOSTNAME})\s+" rf"(?P<used>\d+)"
)

RX_PROGRAM = re.compile(PROGRAM_LINE)
RX_USAGE = re.compile(USAGE_LINE)


def parse(s: str) -> dict:
    """
    Parse lines of the license output with regular expressions
    """
    parsed_data: dict = {}
    lines = s.splitlines()

    for i, line in enumerate(lines):
        parsed_program = RX_PROGRAM.match(line)
        if parsed_program is None:
            continue
        program_data = parsed_program.groupdict()

        if program_data["used"] != "-":
            program_data["used"] = int(program_data["used"])
        program_data["program"] = program_data["program"].lower()

        parsed_data[program_data["program"]] = {
            "total": int(program_data["max"]),
            "used": program_data["used"],
            "uses": [],
        }

        if parsed_data[program_data["program"]]["used"] == "-":
            calculated_used = 0
            for line in lines[i + 1 :]:
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
                calculated_used += int(usage_data["used"])
            parsed_data[program_data["program"]]["used"] = calculated_used

    return parsed_data
