import logging
from unittest import mock
from unittest.mock import patch

from fastapi import HTTPException, status
from pytest import mark, raises

from lm_agent import backend_utils, main


@mark.asyncio
@mock.patch("lm_agent.main.get_license_manager_backend_version")
async def test_backend_version_check__on_non_matching_agent_backend_major_versions(
    mock_license_manager_backend_version: mock.AsyncMock,
):
    """
    Test that the agent starts when the major version returned by the backend matches our own.
    """
    mock_license_manager_backend_version.return_value = "2.5.4"
    p0 = patch.object(main, "AGENT_VERSION", "1.5")
    p1 = patch.object(main.settings, "LOG_LEVEL", "INFO")

    with p0, p1:
        with raises(backend_utils.LicenseManagerBackendVersionError):
            await main.backend_version_check()


@mark.asyncio
async def test_health(agent_client):
    """
    Does a healthcheck endpoint exist?
    """
    resp = await agent_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == dict(message="OK")


@mark.asyncio
async def test_root(agent_client):
    """
    Does a root endpoint exist?
    """
    resp = await agent_client.get("/")
    assert resp.status_code == 200
    assert resp.json() == dict(message="OK")


@mark.asyncio
async def test_reconcile_not_ok(agent_client):
    """
    Does the /reconcile give an error status code when the reconcile method fails?
    """
    with patch.object(
        main,
        "reconcile",
        side_effect=HTTPException(status_code=status.HTTP_400_BAD_REQUEST),
    ):
        resp = await agent_client.get("/reconcile")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


def test_begin_logging():
    """
    Do I configure logging when the app starts up?
    """
    with patch.object(main.settings, "LOG_LEVEL", "CRITICAL"):
        with patch.object(main.logger, "setLevel") as mock_set_level:
            main.begin_logging()
            assert mock_set_level.called_once_with(logging.CRITICAL)
