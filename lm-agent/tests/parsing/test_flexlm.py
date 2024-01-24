"""
Test the flexlm parser
"""
from pytest import mark

from lm_agent.parsing.flexlm import parse


@mark.parametrize(
    "fixture,result",
    [
        (
            "lmstat_output",
            {
                "total": {"feature": "testfeature", "total": 1000, "used": 93},
                "uses": [
                    {"booked": 29, "lead_host": "myserver.example.com", "user_name": "jbemfv"},
                    {"booked": 27, "lead_host": "myserver.example.com", "user_name": "cdxfdn"},
                    {"booked": 37, "lead_host": "myserver.example.com", "user_name": "jbemfv"},
                ],
            },
        ),
        ("lmstat_output_bad", {"total": None, "uses": []}),
    ],
)
def test_parse(request, fixture, result):
    """
    Can we parse good and bad output?
    """
    text = request.getfixturevalue(fixture)
    assert parse(text) == result
