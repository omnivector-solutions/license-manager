import logging
import sys
from unittest.mock import MagicMock, patch

from pytest import mark

from lm_backend import main


@mark.asyncio
async def test_health(backend_client):
    """
    Does a healthcheck endpoint exist?
    """
    resp = await backend_client.get("/health")
    assert resp.status_code == 200


@mark.asyncio
async def test_root(backend_client):
    """
    Does a root endpoint exist?
    """
    resp = await backend_client.get("/")
    assert resp.status_code == 200
    # TODO: If root is ever made to return anything meaningful, we should test that here


def test_begin_logging():
    """
    Do I configure logging when the app starts up?
    """
    with patch.object(main.settings, "LOG_LEVEL", new="CRITICAL"):
        with patch.object(main.logger, "add") as add_method:
            main.begin_logging()
            assert add_method.called_once_with(sys.stderr, level="CRITICAL")

    with patch.object(main.settings, "LOG_LEVEL_SQL", new="WARNING"):
        sqlalchemy_engine_mock = MagicMock()
        databases_mock = MagicMock()
        other_mock = MagicMock()

        def get_mock_logger(name):
            if name == "sqlalchemy.engine":
                return sqlalchemy_engine_mock
            elif name == "databases":
                return databases_mock
            else:
                return other_mock

        with patch.object(
            logging,
            "getLogger",
            side_effect=get_mock_logger,
        ):
            main.begin_logging()

        assert sqlalchemy_engine_mock.called_once_with(logging.WARNING)
        assert databases_mock.called_once_with(logging.WARNING)


@mark.asyncio
async def test_database_events(backend_client):
    """
    Do I connect, create tables, and disconnect the db?
    """
    p_create_all_tables = patch("lm_backend.storage.create_all_tables", autospec=True)
    p_connect = patch("lm_backend.storage.database.connect", autospec=True)
    p_disconnect = patch("lm_backend.storage.database.disconnect", autospec=True)
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
