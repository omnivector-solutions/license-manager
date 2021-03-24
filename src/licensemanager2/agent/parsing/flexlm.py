"""
Parser for flexlm
"""
import re


HOSTWORD = r"[a-zA-Z0-9-]+"
HOSTNAME = rf"{HOSTWORD}(\.{HOSTWORD})*"
NONWS = r"\S+"
INT = r"\d+"
NONPAREN = r"[^() ]+"
MMDD = rf"{INT}/{INT}"
HHMM = rf"{INT}:{INT}"
RX = re.compile(
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


def parse(s: str) -> dict:
    """
    Parse lines of the license output with regular expressions
    """
    ret = []
    for line in s.splitlines():
        parsed = RX.match(line)
        if parsed is None:
            continue
        ret.append(parsed.groupdict())
    return ret
