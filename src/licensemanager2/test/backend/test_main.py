"""
Triggers and handlers in main
"""
import logging
from unittest.mock import ANY, call, patch

from pytest import mark

from licensemanager2.backend import main


@mark.asyncio
async def test_health(backend_client, ok_response):
    """
    Does a healthcheck endpoint exist?
    """
    resp = await backend_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == ok_response.dict()


@mark.asyncio
async def test_root(backend_client, ok_response):
    """
    Does a root endpoint exist?
    """
    resp = await backend_client.get("/")
    assert resp.status_code == 200
    # i'd love to know why resp.json() returns a dict instead of a string, but w/e
    assert resp.json() == ok_response.dict()


def test_begin_logging():
    """
    Do I configure logging when the app starts up?
    """
    p_setLevel = patch("logging.Logger.setLevel", autospec=True)
    p_log_sql = patch.object(main.SETTINGS, "LOG_LEVEL_SQL", None)
    p_log = patch.object(main.SETTINGS, "LOG_LEVEL", "CRITICAL")

    with p_log_sql, p_log, p_setLevel as m_setLevel:
        main.begin_logging()

    assert m_setLevel.call_args_list == [call(ANY, logging.CRITICAL)]

    p_log_sql = patch.object(main.SETTINGS, "LOG_LEVEL_SQL", "DEBUG")
    with p_log_sql, p_log, p_setLevel as m_setLevel:
        main.begin_logging()

    assert m_setLevel.call_args_list == [
        call(ANY, logging.DEBUG),
        call(ANY, logging.DEBUG),
        call(ANY, logging.CRITICAL),
    ]


@mark.asyncio
async def test_database_events():
    """
    Do I connect, create tables, and disconnect the db?
    """
    p_create_all_tables = patch(
        "licensemanager2.backend.storage.create_all_tables", autospec=True
    )
    p_connect = patch("licensemanager2.backend.storage.database.connect", autospec=True)
    p_disconnect = patch(
        "licensemanager2.backend.storage.database.disconnect", autospec=True
    )
    with p_create_all_tables as m_create_all_tables, p_connect as m_connect, p_disconnect as m_disconnect:
        await main.init_database()
        m_create_all_tables.assert_called_once_with()
        m_connect.assert_called_once_with()
        await main.disconnect_database()
        m_disconnect.assert_called_once_with()


def test_handler():
    """
    Check that the handler ends up calling mangum with the original semantics,
    and only when eventContext is present
    """
    p1 = patch.object(main, "Mangum", autospec=True)
    context = 19

    # cloudwatch ping
    event1 = {"ping": True}
    with p1 as m1:
        main.handler(event1, context)
    assert len(m1.return_value.call_args_list) == 0

    # http request
    event2 = {"requestContext": 19}
    with p1 as m1:
        main.handler(event2, context)
    assert m1.return_value.call_args[0] == (event2, context)
