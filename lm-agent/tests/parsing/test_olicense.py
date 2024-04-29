"""
Test the OLicense parser
"""

from lm_agent.parsing.olicense import parse, parse_feature_line, parse_in_use_line, parse_usage_line
from lm_agent.server_interfaces.license_server_interface import LicenseUsesItem


def test_parse_feature_line():
    """
    Does the regex for the feature line match the lines in the output?
    The line contains:
    - feature
    - license type
    - total
    - expiration date
    From these, we only need to extract ``feature`` and ``total``.
    """
    assert parse_feature_line("  ftire_adams;         	FreeFloating;	3;	2022-12-31 23:59:59;") == {
        "feature": "ftire_adams",
        "total": 3,
    }
    assert parse_feature_line("  ftire_adams;         	FreeFloating;	1;	2023-02-28 23:59:00;") == {
        "feature": "ftire_adams",
        "total": 1,
    }
    assert parse_feature_line("not a feature line") is None
    assert parse_feature_line("Licenser:	cosin scientific software") is None
    assert parse_feature_line("") is None


def test_parse_in_use_line():
    """
    Does the regex for the in use line match the lines in the output?
    The line contains:
    - in_use
    """
    assert parse_in_use_line("    2 FloatsLockedBy:") == 2
    assert parse_in_use_line("    1 FloatsLockedBy 'unknown clients'") == 1
    assert parse_in_use_line("not a in use license") is None
    assert parse_in_use_line("") is None


def test_parse_usage_line():
    """
    Does the regex for the usage line match the line in the output?
    The line contains:
    - user name
    - lead host
    - booked
    """
    assert parse_usage_line("        sbhyma@RD0087712 #1") == LicenseUsesItem(
        username="sbhyma",
        lead_host="RD0087712",
        booked=1,
    )
    assert parse_usage_line("        sbhyma@p-c39.maas.rnd.com #1") == LicenseUsesItem(
        username="sbhyma",
        lead_host="p-c39.maas.rnd.com",
        booked=1,
    )
    assert parse_usage_line("not a usage line") is None
    assert parse_usage_line("") is None


def test_parse__correct_output(olicense_output):
    """
    Does the parser return the correct data for this output?
    - olicense_output: expected output from the license server,
    which contain licenses and usage information.
    """
    assert parse(olicense_output) == {
        "ftire_adams": {
            "total": 4,
            "used": 3,
            "uses": [
                LicenseUsesItem(username="sbhyma", lead_host="RD0087712", booked=1),
                LicenseUsesItem(username="sbhyma", lead_host="RD0087713", booked=1),
                LicenseUsesItem(username="user22", lead_host="RD0087713", booked=1),
            ],
        }
    }


def test_parse__bad_output(olicense_output_bad):
    """
    Does the parser return the correct data for this output?
    - olicense_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(olicense_output_bad) == {}


def test_parse__no_licenses_output(olicense_output_no_licenses):
    """
    Does the parser return the correct data for this output?
    - olicense_output_no_licenses: expected output from the server
    when none of the licenses are in use by users.
    """
    assert parse(olicense_output_no_licenses) == {"ftire_adams": {"total": 4, "used": 0, "uses": []}}
