import logging
import sys
from unittest.mock import MagicMock, patch

from fastapi import status
from httpx import AsyncClient
from pytest import mark

from lm_backend import main


@mark.asyncio
async def test_health_check(backend_client: AsyncClient):
    """
    Test the health check route.

    This test ensures the API has a health check path configured properly, so
    the production and staging environments can configure the load balancing
    """

    response = await backend_client.get("/lm/health")

    assert response.status_code == status.HTTP_204_NO_CONTENT


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
