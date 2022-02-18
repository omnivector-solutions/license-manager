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


def parse_program_line(line: str):
    """
    Parse the program line in the LS-Dyna output.
    Data we need:
    - ``program``: license name
    - ``max``: total amount of licenses in the server
    The ``used``value will be evaluated later.
    """
    parsed_program = RX_PROGRAM.match(line)
    if parsed_program is None:
        return None
    program_data = parsed_program.groupdict()
    program_data["program"] = program_data["program"].lower()

    return {
        "program": program_data["program"],
        "total": int(program_data["max"]),
    }


def parse_usage_line(line: str):
    """
    Parse the usage line in the LS-Dyna output.
    Data we need:
    - ``user_name``: user who booked the license
    - ``lead_host``: host using the license
    - ``booked``: quantity of licenses being used

    Obs: this line doesn't include the license name.
    The license in use is the last one parsed before this line.
    """
    parsed_usage = RX_USAGE.match(line)
    if parsed_usage is None:
        return None
    usage_data = parsed_usage.groupdict()

    return {
        "user_name": usage_data["user"],
        "lead_host": usage_data["lead_host"],
        "booked": int(usage_data["used"]),
    }


def parse_total_line(line: str):
    """
    Parse the total line in the LS-Dyna output.
    Data we need:
    - ``used``: quantity of licenses being used in the server

    Obs: all LS-Dyna licenses in the server share the same
    license pool, where the amount of available licenses can be consumed
    by any license in the server.

    The ``used`` value is the sum of all licenses in use in the pool.
    Since we calculate the available quantity as ``available = total - used``,
    we'll use the group ``used`` value for all licenses, so the available
    will reflect the correct amount of free licenses in the pool.
    """
    parsed_total = RX_TOTAL.match(line)
    if parsed_total is None:
        return None
    total_data = parsed_total.groupdict()

    return int(total_data["used"])


def parse(s: str):
    """
    Parse the LS-Dyna output, using regex to match the lines we need:
    - ``program line``: info about each license
    - ``usage line``: info about users using licenses
    - ``total line``: info about the pool, which affects all licenses

    Since the usage line doesn't have the name of the license in use,
    we're saving each parsed license in a list. This way, we can find
    which license the user is using by checking the last parsed license
    in this list.

    Also, all the licenses in the server will have their ``used`` value
    filled with the group used value, since it'll reflect the correct
    amount of free licenses in the pool.
    """
    parsed_data: dict = {}
    program_list: list = []
    group_used: int = 0

    for line in s.splitlines():
        parsed_program = parse_program_line(line)
        parsed_usage = parse_usage_line(line)
        parsed_total = parse_total_line(line)

        if parsed_program:
            parsed_data[parsed_program["program"]] = {
                "total": int(parsed_program["total"]),
                "uses": [],
            }
            program_list.append(parsed_program["program"])

        elif parsed_usage:
            program = program_list[-1]
            parsed_data[program]["uses"].append(parsed_usage)

        elif parsed_total:
            group_used = parsed_total
            break

    for program in parsed_data.keys():
        parsed_data[program]["used"] = group_used

    return parsed_data
