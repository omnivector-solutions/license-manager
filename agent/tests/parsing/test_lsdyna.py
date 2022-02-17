"""
Test the LS-Dyna parser
"""

from lm_agent.parsing.lsdyna import parse, parse_program_line, parse_total_line, parse_usage_line


def test_parse_program_line():
    """
    Does the regex for the program line match the lines in the output?
    The line contains:
    - program
    - expiration date
    - used CPUs
    - free CPUs
    - max CPUs
    - queue
    From these, we only need to extract ``program`` and ``max CPUs``.
    """
    assert parse_program_line("MPPDYNA          12/30/2022          0    500    500 |     0") == {
        "program": "mppdyna",
        "total": 500,
    }
    assert parse_program_line("MPPDYNA_971      12/30/2022          -     60    250 |     0") == {
        "program": "mppdyna_971",
        "total": 250,
    }
    assert parse_program_line("LS-DYNA          12/30/2022          0      0    500 |     0") == {
        "program": "ls-dyna",
        "total": 500,
    }
    assert parse_program_line("LS-DYNA_971      12/30/2022          0      0    500 |     0") == {
        "program": "ls-dyna_971",
        "total": 500,
    }
    assert parse_program_line("not a program line") is None
    assert parse_program_line("MPPDYNA          12/30/2022          0") is None
    assert parse_program_line("") is None


def test_parse_usage_line():
    """
    Does the regex for the usage line match the lines in the output?
    The line contains:
    - user
    - port
    - host
    - used CPUs
    From these, we only need to extract ``user``, ``host``, ``used CPUs``.
    """
    assert parse_usage_line(" ywazrn     91665@n-c51.maas.rnd.com  80") == {
        "user_name": "ywazrn",
        "lead_host": "n-c51.maas.rnd.com",
        "booked": 80,
    }
    assert parse_usage_line(" ndhtw9     91665@n-c55.maas.rnd.com  40") == {
        "user_name": "ndhtw9",
        "lead_host": "n-c55.maas.rnd.com",
        "booked": 40,
    }
    assert parse_usage_line(" ywazrn     not-a-host  80") is None
    assert parse_usage_line(" ndhtw9     91665@n-c55.maas.rnd.com") is None
    assert parse_usage_line("91665@n-c55.maas.rnd.com  20") is None
    assert parse_usage_line("") is None


def test_parse_total_line():
    """
    Does the regex for the total line match the line in the output?
    The line contains:
    - "LICENSE GROUP" string
    - used CPUs
    - free CPUs
    - max CPUs
    - queue
    From these, we only need to extract ``used CPUs``.
    """
    assert parse_total_line("                   LICENSE GROUP   440     60    500 |     0") == 440
    assert parse_total_line("                   LICENSE GROUP     0    000    500 |     0") == 0
    assert parse_total_line("                   0    000    500 |     0") is None
    assert parse_total_line("                   LICENSE GROUP     0") is None
    assert parse_total_line("") is None


def test_parse__correct_output(lsdyna_output):
    """
    Does the parser return the correct data for this output?
    - lsdyna_output: expected output from the license server,
    which contain licenses and usage information.
    """
    assert parse(lsdyna_output) == {
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
        "mppdyna_971": {"total": 500, "used": 440, "uses": []},
        "mppdyna_970": {"total": 500, "used": 440, "uses": []},
        "mppdyna_960": {"total": 500, "used": 440, "uses": []},
        "ls-dyna": {"total": 500, "used": 440, "uses": []},
        "ls-dyna_971": {"total": 500, "used": 440, "uses": []},
        "ls-dyna_970": {"total": 500, "used": 440, "uses": []},
        "ls-dyna_960": {"total": 500, "used": 440, "uses": []},
    }


def test_parse__bad_output(lsdyna_output_bad):
    """
    Does the parser return the correct data for this output?
    - lsdyna_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(lsdyna_output_bad) == {}


def test_parse__no_licenses_output(lsdyna_output_no_licenses):
    """
    Does the parser return the correct data for this output?
    - lsdyna_output_no_licenses: expected output from the server
    when none of the licenses are in use by users.
    """
    assert parse(lsdyna_output_no_licenses) == {
        "mppdyna": {"total": 500, "used": 0, "uses": []},
        "mppdyna_971": {"total": 500, "used": 0, "uses": []},
        "mppdyna_970": {"total": 500, "used": 0, "uses": []},
        "mppdyna_960": {"total": 500, "used": 0, "uses": []},
        "ls-dyna": {"total": 500, "used": 0, "uses": []},
        "ls-dyna_971": {"total": 500, "used": 0, "uses": []},
        "ls-dyna_970": {"total": 500, "used": 0, "uses": []},
        "ls-dyna_960": {"total": 500, "used": 0, "uses": []},
    }
