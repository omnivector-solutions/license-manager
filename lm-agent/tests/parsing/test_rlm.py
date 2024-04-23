"""
Test the RLM parser
"""
from pytest import mark

from lm_agent.parsing.rlm import parse, parse_count_line, parse_feature_line, parse_usage_line


def test_parse_feature_line():
    """
    Does the regex for the feature line match the lines in the output?
    The line contains:
    - feature
    - version

    From these, we only need to extract ``feature``.
    """
    assert parse_feature_line("powercase v1.0") == "powercase"
    assert parse_feature_line("powerflow-decomp v1.0") == "powerflow-decomp"
    assert parse_feature_line("powerdelta-translate2 v1.0") == "powerdelta-translate2"
    assert parse_feature_line("not a feature line") is None
    assert parse_feature_line("Copyright (C) 2006-2017, Reprise Software, Inc. All rights reserved.") is None
    assert parse_feature_line("") is None


def test_parse_count_line():
    """
    Does the regex for the count line match the lines in the output?
    The line contains:
    - count
    - in_use
    """
    assert parse_count_line("count: 5, # reservations: 0, inuse: 3, exp: 31-dec-2023") == {
        "count": 5,
        "in_use": 3,
    }
    assert parse_count_line("count: 3000, # reservations: 0, inuse: 0, exp: 31-dec-2023") == {
        "count": 3000,
        "in_use": 0,
    }
    assert parse_count_line("count: 1000000, # reservations: 0, inuse: 0, exp: 31-dec-2023") == {
        "count": 1000000,
        "in_use": 0,
    }
    assert parse_count_line("aaaaa of bbbbbbb licenses") is None
    assert parse_count_line("") is None


def test_parse_usage_line():
    """
    Does the regex for the usage line match the line in the output?
    The line contains:
    - feature
    - user name
    - lead host
    - booked
    """
    assert parse_usage_line(
        "converge_super v3.0: asdj13@myserver.example.com 29/0 at 11/01 09:01  (handle: 15a)"
    ) == {
        "license_feature": "converge_super",
        "username": "asdj13",
        "lead_host": "myserver.example.com",
        "booked": 29,
    }
    assert parse_usage_line("powercase v1.0: dfsdgv@server1 1/0 at 08/15 09:34  (handle: 182)") == {
        "license_feature": "powercase",
        "username": "dfsdgv",
        "lead_host": "server1",
        "booked": 1,
    }
    assert parse_usage_line("aaaaa") is None
    assert parse_usage_line("") is None


@mark.parametrize(
    "fixture,result",
    [
        (
            "rlm_output",
            {
                "converge": {
                    "total": 1,
                    "used": 0,
                    "uses": [],
                },
                "converge_gui": {"total": 45, "used": 0, "uses": []},
                "converge_gui_polygonica": {"total": 1, "used": 0, "uses": []},
                "converge_super": {
                    "total": 1000,
                    "used": 93,
                    "uses": [
                        {
                            "booked": 29,
                            "lead_host": "myserver.example.com",
                            "username": "asdj13",
                        },
                        {
                            "booked": 27,
                            "lead_host": "myserver.example.com",
                            "username": "cddcp2",
                        },
                        {
                            "booked": 37,
                            "lead_host": "myserver.example.com",
                            "username": "asdj13",
                        },
                    ],
                },
                "converge_tecplot": {"total": 45, "used": 0, "uses": []},
            },
        ),
        (
            "another_rlm_output",
            {
                "powercase": {
                    "used": 3,
                    "total": 5,
                    "uses": [
                        {"username": "dfsdgv", "lead_host": "server1", "booked": 1},
                        {"username": "addvbh", "lead_host": "server2", "booked": 1},
                        {"username": "wrtgb3", "lead_host": "server3", "booked": 1},
                    ],
                },
                "powerexport": {"used": 0, "total": 5, "uses": []},
                "powerflow-decomp": {"used": 0, "total": 3000, "uses": []},
                "powerflow-disc": {"used": 0, "total": 3000, "uses": []},
                "powerinsight": {"used": 0, "total": 5, "uses": []},
                "powerviz": {"used": 0, "total": 5, "uses": []},
                "powerviz-generator": {"used": 0, "total": 2, "uses": []},
                "powerviz-soiling": {"used": 0, "total": 7, "uses": []},
                "exasignalprocessingjob": {"used": 0, "total": 6, "uses": []},
                "poweracoustics": {"used": 0, "total": 1, "uses": []},
                "powercool": {"used": 0, "total": 1, "uses": []},
                "powerdelta": {
                    "used": 1,
                    "total": 1,
                    "uses": [{"username": "ghnds2", "lead_host": "server4", "booked": 1}],
                },
                "powerdelta-meshunion": {"used": 0, "total": 1, "uses": []},
                "powerdelta-translate2": {"used": 0, "total": 1000000, "uses": []},
                "powerflow-sim": {"used": 0, "total": 7000, "uses": []},
                "powerinsight-generator": {"used": 0, "total": 1, "uses": []},
                "powerthermconnector": {"used": 0, "total": 1, "uses": []},
                "powertherm": {"used": 0, "total": 1, "uses": []},
                "powertherm-mp": {"used": 0, "total": 3, "uses": []},
                "powertherm-multigrid": {"used": 0, "total": 1, "uses": []},
                "powertherm-sc": {"used": 0, "total": 1, "uses": []},
                "powertherm-solver": {"used": 0, "total": 1, "uses": []},
            },
        ),
    ],
)
def test_parse__correct_ouput(request, fixture, result):
    """
    Does the parser return the correct data for this output?
    - rlm_output: expected output from the license server,
    which contain licenses and usage information.
    """
    output = request.getfixturevalue(fixture)
    assert parse(output) == result


def test_parse__bad_output(rlm_output_bad):
    """
    Does the parser return the correct data for this output?
    - rlm_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(rlm_output_bad) == {}


def test_parse__no_licenses_output(rlm_output_no_licenses):
    """
    Does the parser return the correct data for this output?
    - rlm_output_no_licenses: expected output from the server
    when none of the licenses are in use by users.
    """
    assert parse(rlm_output_no_licenses) == {
        "converge": {"total": 1, "used": 0, "uses": []},
        "converge_gui": {"total": 45, "used": 0, "uses": []},
        "converge_gui_polygonica": {"total": 1, "used": 0, "uses": []},
        "converge_super": {"total": 1000, "used": 0, "uses": []},
        "converge_tecplot": {"total": 45, "used": 0, "uses": []},
    }
