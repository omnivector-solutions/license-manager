"""
Parser for flexlm
"""
import re

HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
NONWS = r"\S+"
NONCOLON = r"[^:]+"
INT = r"\d+"
NONPAREN = r"[^() ]+"
MMDD = rf"{INT}/{INT}"
HHMM = rf"{INT}:{INT}"

DATA_LINE = (
    r"^\s+"
    rf"(?P<user>{NONWS}) "
    rf"(?P<user_host>{HOSTNAME}) "
    rf"(?P<tty>{NONWS}) "
    rf"\((?P<version>{NONPAREN})\) "
    r"\("
    rf"(?P<license_host>{HOSTNAME})/"
    rf"(?P<license_port>{INT}) "
    rf"(?P<license_pid>{INT})"
    r"\), start "
    rf"(?P<weekday>{NONWS}) "
    rf"(?P<date>{MMDD}) "
    rf"(?P<time>{HHMM}), "
    rf"(?P<tokens>{INT}) "
    r"licenses$"
)

TOTALS_LINE = (
    r"^Users of "
    rf"(?P<feature>{NONCOLON}):  "
    r"\(Total of "
    rf"(?P<total>{INT}) "
    r"licenses issued;  Total of "
    rf"(?P<used>{INT}) "
    rf"licenses in use\)$"
)


RX = re.compile(rf"{DATA_LINE}|{TOTALS_LINE}")


def parse(s: str) -> dict:
    """
    Parse lines of the license output with regular expressions
    """
    parsed_data: dict = {"uses": [], "total": None}
    for line in s.splitlines():
        parsed = RX.match(line)
        if parsed is None:
            continue

        if parsed.group("total"):
            d = parsed.groupdict()
            parsed_data["total"] = {
                "total": int(d["total"]),
                "used": int(d["used"]),
                "feature": d["feature"].lower(),
            }
        if parsed.group("user"):
            d = parsed.groupdict()
            parsed_data["uses"].append(
                {
                    "user_name": d["user"],
                    "lead_host": d["user_host"],
                    "booked": int(d["tokens"]),
                }
            )
    return parsed_data
