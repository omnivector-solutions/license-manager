"""
Test the flexlm parser
"""
from textwrap import dedent

from pytest import fixture, mark

from app.parsing.flexlm import parse


@fixture
def lm_output_bad():
    """
    Some unparseable lmstat output
    """
    return dedent(
        """\
    lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
    Flexible License Manager status on Wed 03/31/2021 09:12

    Error getting status: Cannot connect to license server (-15,570:111 "Connection refused")
    """
    )


@fixture
def lm_output():
    """
    Some lmstat output to parse
    """
    return dedent(
        """\
        lmstat - Copyright (c) 1989-2004 by Macrovision Corporation. All rights reserved.
        ...

        Users of TESTFEATURE:  (Total of 1000 licenses issued;  Total of 93 licenses in use)

        ...


        """
        "           jbemfv myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 29 licenses\n"
        "           cdxfdn myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 27 licenses\n"
        "           jbemfv myserver.example.com /dev/tty (v62.2) (myserver.example.com/24200 12507), "
        "start Thu 10/29 8:09, 37 licenses\n"
    )


@mark.parametrize(
    "fixture,result",
    [
        ("lm_output", {"feature": "TESTFEATURE", "total": 1000, "used": 93}),
        ("lm_output_bad", {}),
    ],
)
def test_parse(request, fixture, result):
    """
    Can we parse good and bad output?
    """
    text = request.getfixturevalue(fixture)
    assert parse(text) == result
