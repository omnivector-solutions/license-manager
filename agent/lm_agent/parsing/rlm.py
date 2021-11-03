"""
Parser for rlm
"""
import re

INT = r"\d+"
VERSION = rf"v{INT}\.{INT}"
HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTWORD2 = r"[a-zA-Z0-9-.]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD2})*"

TOTALS_LINE = rf"^(?P<license_feature>\w+) {VERSION}: (?P<user_name>\w+)@(?P<lead_host>{HOSTNAME}) (?P<license_used_by_host>\d+).*$"  # noqa
DATA_LINE = rf"^\s*(?P<license_feature>\w+) {VERSION}$"
COUNT_LINE = r"^\s*count: (?P<count>\d+).*inuse: (?P<in_use>\d+).*$"

RX_TOTAL = re.compile(rf"{TOTALS_LINE}")
RX_DATA = re.compile(rf"{DATA_LINE}")
RX_COUNT = re.compile(rf"{COUNT_LINE}")


def _get_start_offset(lines) -> int:
    """Get the start offset of the license data."""
    i = len(lines) - 1
    count = 0
    for line in lines[::-1]:
        if "-" * 10 in line:
            count += 1
        if count == 2:
            break
        i -= 1
    return i


def parse(s: str) -> dict:
    """
    Parse lines of the license output with regular expressions
    """
    parsed_dict: dict = {"uses": [], "total": []}
    start_offset = _get_start_offset(s.splitlines())
    lines = [line.strip() for line in s.splitlines()[start_offset:]]

    for i, line in enumerate(lines):
        parsed_total = RX_TOTAL.match(line)
        parsed_data = RX_DATA.match(line)
        if parsed_total:
            total_data = parsed_total.groupdict()
            parsed_dict["uses"].append(
                {
                    "user_name": total_data["user_name"],
                    "lead_host": total_data["lead_host"],
                    "booked": int(total_data["license_used_by_host"]),
                    "feature": total_data["license_feature"],
                }
            )
        elif parsed_data:
            parsed_count = RX_COUNT.match(lines[i + 1])
            count_data = parsed_count.groupdict()
            data_data = parsed_data.groupdict()
            parsed_dict["total"].append(
                {
                    "feature": data_data["license_feature"],
                    "total": int(count_data["count"]),
                    "used": int(count_data["in_use"]),
                }
            )
        else:
            continue

    return parsed_dict
