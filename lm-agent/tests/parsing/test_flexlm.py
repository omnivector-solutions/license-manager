"""
Test the flexlm parser
"""
from pytest import mark

from lm_agent.parsing.flexlm import parse, parse_feature_line, parse_usage_line


@mark.parametrize(
    "line,result",
    [
        (
            "Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 93 licenses in use)",
            {
                "feature": "testfeature",
                "total": 1000,
                "used": 93,
            },
        ),
        (
            "not a feature line",
            None,
        ),
        (
            "",
            None,
        ),
    ],
)
def test_parse_feature_line(line, result):
    """
    Does the regex for the feature line match the lines in the output?

    The line contains:
    - feature
    - total
    - used
    """
    assert parse_feature_line(line) == result


@mark.parametrize(
    "line,result",
    [
        (
            "    user1 myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), start Thu 10/29 8:09, 29 licenses",
            {
                "username": "user1",
                "lead_host": "myserver.example.com",
                "booked": 29,
            },
        ),
        (
            "    user2 another.server.com /dev/tty feature=feature (v2023.0) (another.server.com/41020 10223), start Mon 3/11 13:16, 100 licenses",
            {
                "username": "user2",
                "lead_host": "another.server.com",
                "booked": 100,
            },
        ),
        (
            "    user3 ER1234 SESOD5045 MSCONE:ADAMS_View (v2023.0331) (alternative.server.com/29065 2639), start Fri 3/8 13:25, 5 licenses",
            {
                "username": "user3",
                "lead_host": "ER1234",
                "booked": 5,
            },
        ),
        (
            "    user3 ER1234 SESOD5045 MSCONE:ADAMS_View (v2023.0331) (alternative.server.com/29065 2639), start Fri 3/8 13:25",
            {
                "username": "user3",
                "lead_host": "ER1234",
                "booked": 1,
            },
        ),
        ("aaaaa", None),
    ],
)
def test_parse_usage_line(line, result):
    """
    Does the regex for the usage line match the line in the output?

    The line contains:
    - user name
    - lead host
    - booked
    """
    assert parse_usage_line(line) == result


@mark.parametrize(
    "fixture,result",
    [
        (
            "flexlm_output",
            {
                "feature": "testfeature",
                "total": 1000,
                "used": 93,
                "uses": [
                    {"booked": 29, "lead_host": "myserver.example.com", "username": "sdmfva"},
                    {"booked": 27, "lead_host": "myserver.example.com", "username": "adfdna"},
                    {"booked": 37, "lead_host": "myserver.example.com", "username": "sdmfva"},
                ],
            },
        ),
        (
            "flexlm_output_2",
            {
                "feature": "test_feature",
                "total": 42800,
                "used": 1600,
                "uses": [
                    {"booked": 100, "lead_host": "p-c94.com", "username": "usbn12"},
                    {"booked": 1400, "lead_host": "p-c94.com", "username": "usbn12"},
                    {"booked": 100, "lead_host": "p-c94.com", "username": "usbn12"},
                ],
            },
        ),
        (
            "flexlm_output_3",
            {
                "feature": "ccmppower",
                "total": 40,
                "used": 3,
                "uses": [
                    {"booked": 1, "lead_host": "dcv033.com", "username": "1nou7p"},
                    {"booked": 1, "lead_host": "n-c41.com", "username": "1nou7p"},
                    {"booked": 1, "lead_host": "nid001234", "username": "1nou7p"},
                ],
            },
        ),
        (
            "flexlm_output_4",
            {
                "feature": "mscone",
                "total": 750,
                "used": 18,
                "uses": [
                    {"booked": 5, "lead_host": "ER0037", "username": "abcdkk"},
                    {"booked": 1, "lead_host": "ER0037", "username": "abcdkk"},
                    {"booked": 5, "lead_host": "ER0037", "username": "abcdkk"},
                    {"booked": 1, "lead_host": "ER0037", "username": "abcdkk"},
                    {"booked": 5, "lead_host": "ER0037", "username": "abcdkk"},
                    {"booked": 1, "lead_host": "ER0037", "username": "abcdkk"},
                ],
            },
        ),
    ],
)
def test_parse__correct_output(request, fixture, result):
    """
    Does the parser return the correct data for this output?

    - flexlm_output: expected output from the license server,
    which contain licenses and usage information.
    """
    output = request.getfixturevalue(fixture)
    assert parse(output) == result


def test_parse__bad_output(flexlm_output_bad):
    """
    Does the parser return the correct data for this output?

    - flexlm_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(flexlm_output_bad) == {}


def test_parse__not_licenses_output(flexlm_output_no_licenses):
    """
    Does the parser return the correct data for this output?

    - flexlm_output_no_licenses: expected output from the license server,
    when none of the licenses are in use by users.
    """
    assert parse(flexlm_output_no_licenses) == {
        "feature": "testfeature",
        "total": 1000,
        "used": 0,
        "uses": [],
    }
