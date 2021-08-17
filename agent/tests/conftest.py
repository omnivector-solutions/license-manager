"""
Configuration of pytest for agent tests
"""
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import respx
from httpx import ASGITransport, AsyncClient
from pytest import fixture

from lm_agent.config import settings
from lm_agent.main import app as agent_app


@fixture
async def agent_client():
    """
    A client that can issue fake requests against endpoints in the agent
    """
    ac = AsyncClient(
        transport=ASGITransport(app=agent_app, raise_app_exceptions=False),
        base_url="http://test",
        headers={"authorization": "bearer xxx.xxx.xxx"},
    )
    async with ac:
        yield ac


MOCK_BIN_PATH = Path(__file__).parent / "mock_tools"


@fixture
def license_servers():
    return ["172.0.1.2 2345", "172.0.1.3 2345"]


@fixture(autouse=True)
def backend_setting():
    """
    Force a specific host for the backend
    """
    with patch.multiple(settings, BACKEND_BASE_URL="http://backend", BIN_PATH=MOCK_BIN_PATH) as mck:
        yield mck


@fixture
def respx_mock():
    """
    Run a test in the respx context (similar to respx decorator, but it's a fixture)
    """
    with respx.mock as mock:
        yield mock


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
