"""
Test the rlm parser
"""
from pytest import mark

from lm_agent.parsing.rlm import _get_start_offset, parse


@mark.parametrize(
    "fixture,result",
    [
        (
            "rlm_output",
            {
                "total": [
                    {"feature": "converge", "total": 1, "used": 0},
                    {"feature": "converge_gui", "total": 45, "used": 0},
                    {"feature": "converge_gui_polygonica", "total": 1, "used": 0},
                    {"feature": "converge_super", "total": 1000, "used": 93},
                    {"feature": "converge_tecplot", "total": 45, "used": 0},
                ],
                "uses": [
                    {
                        "booked": 29,
                        "lead_host": "myserver.example.com",
                        "user_name": "jbemfv",
                        "feature": "converge_super",
                    },
                    {
                        "booked": 27,
                        "lead_host": "myserver.example.com",
                        "user_name": "cdxfdn",
                        "feature": "converge_super",
                    },
                    {
                        "booked": 37,
                        "lead_host": "myserver.example.com",
                        "user_name": "jbemfv",
                        "feature": "converge_super",
                    },
                ],
            },
        ),
        ("lm_output_bad", {"total": [], "uses": []}),
    ],
)
def test_parse(request, fixture, result):
    """
    Can we parse good and bad output?
    """
    text = request.getfixturevalue(fixture)
    assert parse(text) == result


@mark.parametrize("fixture,result", [("rlm_output", 41), ("lm_output_bad", 0)])
def test_get_start_offset(request, fixture, result):
    """
    Test the function that returns the offset for the RLM parser
    """
    text = request.getfixturevalue(fixture)
    assert result == _get_start_offset(text.splitlines())
