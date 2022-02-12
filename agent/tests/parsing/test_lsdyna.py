"""
Test the LS-Dyna parser
"""
from pytest import mark

from lm_agent.parsing.lsdyna import parse


@mark.parametrize(
    "fixture,result",
    [
        (
            "lsdyna_output",
            {
                "mppdyna": {
                    "total": 500,
                    "used": 440,
                    "uses": [
                        {"user_name": "fane8y", "lead_host": "n-c13.maas.rnd.com", "booked": 80},
                        {"user_name": "ssskmj", "lead_host": "n-c52.maas.rnd.com", "booked": 80},
                        {"user_name": "ssskmj", "lead_host": "n-c15.maas.rnd.com", "booked": 80},
                        {"user_name": "ywazrn", "lead_host": "n-c53.maas.rnd.com", "booked": 80},
                        {"user_name": "ywazrn", "lead_host": "n-c51.maas.rnd.com", "booked": 80},
                        {"user_name": "ndhtw9", "lead_host": "n-c55.maas.rnd.com", "booked": 40},
                    ],
                },
                "mppdyna_971": {"total": 500, "used": 0, "uses": []},
                "mppdyna_970": {"total": 500, "used": 0, "uses": []},
                "mppdyna_960": {"total": 500, "used": 0, "uses": []},
                "ls-dyna": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_971": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_970": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_960": {"total": 500, "used": 0, "uses": []},
            },
        ),
        ("lsdyna_output_bad", {}),
        (
            "lsdyna_output_no_licenses",
            {
                "mppdyna": {"total": 500, "used": 0, "uses": []},
                "mppdyna_971": {"total": 500, "used": 0, "uses": []},
                "mppdyna_970": {"total": 500, "used": 0, "uses": []},
                "mppdyna_960": {"total": 500, "used": 0, "uses": []},
                "ls-dyna": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_971": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_970": {"total": 500, "used": 0, "uses": []},
                "ls-dyna_960": {"total": 500, "used": 0, "uses": []},
            },
        ),
    ],
)
def test_parse(request, fixture, result):
    """
    Can we parse good and bad output?
    """
    text = request.getfixturevalue(fixture)
    assert parse(text) == result
