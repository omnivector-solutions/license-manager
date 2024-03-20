"""
Test the LM-X parser
"""

from pytest import mark

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
    assert parse_feature_line("Feature: CatiaV5Reader Version: 21.0 Vendor: ALTAIR") == "catiav5reader"
    assert parse_feature_line("Feature: GlobalZoneEU Version: 21.0 Vendor: ALTAIR") == "globalzoneeu"
    assert parse_feature_line("Feature: HWAIFPBS Version: 21.0 Vendor: ALTAIR") == "hwaifpbs"
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


def test_parse_usage_line():
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
    assert parse_usage_line("1 license(s) used by mbrzy5@dcv046.com_ver2023 [10.123.321.20]") == {
        "user_name": "mbrzy5",
        "lead_host": "dcv046.com",
        "booked": 1,
    }
    assert parse_usage_line("1 license(s) used by k12dca@ms0904_ver5.4.1 [10.123.321.156]") == {
        "user_name": "k12dca",
        "lead_host": "ms0904",
        "booked": 1,
    }
    assert parse_usage_line("0 license(s) used by v-c54.aaa.aa") is None
    assert parse_usage_line("") is None


@mark.parametrize(
    "fixture,result",
    [
        (
            "lmx_output",
            {
                "catiav5reader": {"total": 3, "used": 0, "uses": []},
                "globalzoneeu": {
                    "total": 1000003,
                    "used": 40000,
                    "uses": [
                        {"user_name": "VRAAFG", "lead_host": "RD0082879", "booked": 15000},
                        {"user_name": "VRAAFG", "lead_host": "RD0082879", "booked": 25000},
                    ],
                },
                "hwaifpbs": {"total": 2147483647, "used": 0, "uses": []},
                "hwawpf": {"total": 2147483647, "used": 0, "uses": []},
                "hwactivate": {"total": 2147483647, "used": 0, "uses": []},
                "hwflux2d": {
                    "total": 2147483647,
                    "used": 30000,
                    "uses": [
                        {"user_name": "VRAAFG", "lead_host": "RD0082879", "booked": 15000},
                        {"user_name": "VRAAFG", "lead_host": "RD0082879", "booked": 15000},
                    ],
                },
                "hyperworks": {
                    "total": 1000000,
                    "used": 25000,
                    "uses": [
                        {"user_name": "sssaah", "lead_host": "RD0082406", "booked": 25000},
                    ],
                },
            },
        ),
        (
            "lmx_output_2",
            {
                "femfat_visualizer": {
                    "total": 2,
                    "used": 2,
                    "uses": [
                        {"booked": 1, "lead_host": "dcv046.com", "user_name": "fdsva1"},
                        {"booked": 1, "lead_host": "dcv048.com", "user_name": "asdsc1"},
                    ],
                },
            },
        ),
    ],
)
def test_parse__correct_output(request, fixture, result):
    """
    Does the parser return the correct data for this output?
    - lmx_output: expected output from the license server,
    which contain licenses and usage information.
    """
    output = request.getfixturevalue(fixture)
    assert parse(output) == result


def test_parse__bad_output(lmx_output_bad):
    """
    Does the parser return the correct data for this output?
    - lmx_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(lmx_output_bad) == {}


def test_parse__no_licenses_output(lmx_output_no_licenses):
    """
    Does the parser return the correct data for this output?
    - lmx_output_no_licenses: expected output from the server
    when none of the licenses are in use by users.
    """
    assert parse(lmx_output_no_licenses) == {
        "catiav5reader": {"total": 3, "used": 0, "uses": []},
        "globalzoneeu": {"total": 1000003, "used": 0, "uses": []},
        "hwaifpbs": {"total": 2147483647, "used": 0, "uses": []},
        "hwawpf": {"total": 2147483647, "used": 0, "uses": []},
        "hwactivate": {"total": 2147483647, "used": 0, "uses": []},
        "hwflux2d": {"total": 2147483647, "used": 0, "uses": []},
        "hyperworks": {"total": 1000000, "used": 0, "uses": []},
    }
