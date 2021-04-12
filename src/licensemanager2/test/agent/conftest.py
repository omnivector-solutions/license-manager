"""
Configuration of pytest for agent tests
"""
from unittest.mock import patch

from httpx import AsyncClient
import pkg_resources
from pytest import fixture
import respx

from licensemanager2.agent.main import app as agent_app
from licensemanager2.agent.settings import SETTINGS


@fixture
async def agent_client():
    """
    A client that can issue fake requests against endpoints in the agent
    """
    ac = AsyncClient(
        app=agent_app,
        base_url="http://test",
        headers={"authorization": "bearer xxx.xxx.xxx"},
    )
    async with ac:
        yield ac


MOCK_BIN_PATH = pkg_resources.resource_filename(
    "licensemanager2.test.agent", "mock_tools"
)


@fixture(autouse=True)
def backend_setting():
    """
    Force a specific host for the backend
    """
    with patch.multiple(
        SETTINGS, BACKEND_BASE_URL="http://backend", BIN_PATH=MOCK_BIN_PATH
    ) as mck:
        yield mck


@fixture
def respx_mock():
    """
    Run a test in the respx context (similar to respx decorator, but it's a fixture)
    """
    with respx.mock as mock:
        yield mock
