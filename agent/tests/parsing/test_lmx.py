"""
Test the LM-X parser
"""

from lm_agent.parsing.lmx import parse, parse_feature_line, parse_in_use_line, parse_usage_line


def test_parse_feature_line():
    """
    Does the regex for the feature line match the lines in the output?
    The line contains:
    - feature
    - version
    - vendor
    From these, we only need to extract ``feature``.
    """
    assert parse_feature_line("Feature: CatiaV5Reader Version: 21.0 Vendor: ALTAIR") == "CatiaV5Reader"
    assert parse_feature_line("Feature: GlobalZoneEU Version: 21.0 Vendor: ALTAIR") == "GlobalZoneEU"
    assert parse_feature_line("Feature: HWAIFPBS Version: 21.0 Vendor: ALTAIR") == "HWAIFPBS"
    assert parse_feature_line("not a feature line") is None
    assert parse_feature_line("Version: 21.0 Vendor: ALTAIR") is None
    assert parse_feature_line("") is None


def test_parse_in_use_line():
    """
    Does the regex for the in use line match the lines in the output?
    The line contains:
    - in_use
    - total
    """
    assert parse_in_use_line("0 of 3 license(s) used") == {
        "used": 0,
        "total": 3,
    }
    assert parse_in_use_line("288000 of 1000003 license(s) used:") == {
        "used": 288000,
        "total": 1000003,
    }
    assert parse_in_use_line("aaaaa of bbbbbbb licenses") is None
    assert parse_in_use_line("") is None


def test_usage_line():
    """
    Does the regex for the usage line match the line in the output?
    The line contains:
    - user name
    - lead host
    - booked
    """
    assert parse_usage_line("15000 license(s) used by VRAAFG@RD0082879 [138.106.159.158]") == {
        "user_name": "VRAAFG",
        "lead_host": "RD0082879",
        "booked": 15000,
    }
    assert parse_usage_line("25000 license(s) used by sbak8y@p-c39.maas.rnd.com [10.104.193.54]") == {
        "user_name": "sbak8y",
        "lead_host": "p-c39.maas.rnd.com",
        "booked": 25000,
    }
    assert parse_usage_line("15000 license(s) used by sssegm@p-g2.maas.rnd.com [10.104.192.204]") == {
        "user_name": "sssegm",
        "lead_host": "p-g2.maas.rnd.com",
        "booked": 15000,
    }
    assert parse_usage_line("0 license(s) used by v-c54.aaa.aa") is None
    assert parse_usage_line("") is None


# def test_parse__correct_output(lsdyna_output):
#     """
#     Does the parser return the correct data for this output?
#     - lsdyna_output: expected output from the license server,
#     which contain licenses and usage information.
#     """
#     assert parse(lsdyna_output) == {
#         "mppdyna": {
#             "total": 500,
#             "used": 440,
#             "uses": [
#                 {"user_name": "fane8y", "lead_host": "n-c13.maas.rnd.com", "booked": 80},
#                 {"user_name": "ssskmj", "lead_host": "n-c52.maas.rnd.com", "booked": 80},
#                 {"user_name": "ssskmj", "lead_host": "n-c15.maas.rnd.com", "booked": 80},
#                 {"user_name": "ywazrn", "lead_host": "n-c53.maas.rnd.com", "booked": 80},
#                 {"user_name": "ywazrn", "lead_host": "n-c51.maas.rnd.com", "booked": 80},
#                 {"user_name": "ndhtw9", "lead_host": "n-c55.maas.rnd.com", "booked": 40},
#             ],
#         },
#         "mppdyna_971": {"total": 500, "used": 440, "uses": []},
#         "mppdyna_970": {"total": 500, "used": 440, "uses": []},
#         "mppdyna_960": {"total": 500, "used": 440, "uses": []},
#         "ls-dyna": {"total": 500, "used": 440, "uses": []},
#         "ls-dyna_971": {"total": 500, "used": 440, "uses": []},
#         "ls-dyna_970": {"total": 500, "used": 440, "uses": []},
#         "ls-dyna_960": {"total": 500, "used": 440, "uses": []},
#     }


# def test_parse__bad_output(lsdyna_output_bad):
#     """
#     Does the parser return the correct data for this output?
#     - lsdyna_output_bad: unparseable output from the license server,
#     which can happen when a connection error occours.
#     """
#     assert parse(lsdyna_output_bad) == {}


# def test_parse__no_licenses_output(lsdyna_output_no_licenses):
#     """
#     Does the parser return the correct data for this output?
#     - lsdyna_output_no_licenses: expected output from the server
#     when none of the licenses are in use by users.
#     """
#     assert parse(lsdyna_output_no_licenses) == {
#         "mppdyna": {"total": 500, "used": 0, "uses": []},
#         "mppdyna_971": {"total": 500, "used": 0, "uses": []},
#         "mppdyna_970": {"total": 500, "used": 0, "uses": []},
#         "mppdyna_960": {"total": 500, "used": 0, "uses": []},
#         "ls-dyna": {"total": 500, "used": 0, "uses": []},
#         "ls-dyna_971": {"total": 500, "used": 0, "uses": []},
#         "ls-dyna_970": {"total": 500, "used": 0, "uses": []},
#         "ls-dyna_960": {"total": 500, "used": 0, "uses": []},
#     }
