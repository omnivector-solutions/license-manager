"""
Configuration of pytest for agent tests
"""
from pathlib import Path
from unittest.mock import patch

import pkg_resources
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
