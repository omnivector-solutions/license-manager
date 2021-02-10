"""
Triggers and handlers in main
"""
import logging
from unittest.mock import ANY, call, patch

from pytest import mark

from licensemanager2.agent import main


@mark.asyncio
async def test_health(agent_client, ok_response):
    """
    Does a healthcheck endpoint exist?
    """
    resp = await agent_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == ok_response.dict()


@mark.asyncio
async def test_root(agent_client, ok_response):
    """
    Does a root endpoint exist?
    """
    resp = await agent_client.get("/")
    assert resp.status_code == 200
    # i'd love to know why resp.json() returns a dict instead of a string, but w/e
    assert resp.json() == ok_response.dict()


def test_begin_logging():
    """
    Do I configure logging when the app starts up?
    """
    p_setLevel = patch("logging.Logger.setLevel", autospec=True)
    p_log = patch.object(main.SETTINGS, "LOG_LEVEL", "CRITICAL")

    with p_log, p_setLevel as m_setLevel:
        main.begin_logging()

    assert m_setLevel.call_args_list == [call(ANY, logging.CRITICAL)]
