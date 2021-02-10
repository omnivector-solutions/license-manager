"""
Pytest common fixtures and pytest session configuration
"""
import logging
import os

from httpx import AsyncClient
from pytest import fixture

from licensemanager2.backend.settings import SETTINGS


TESTING_DB_FILE = "./sqlite-testing.db"
SETTINGS.DATABASE_URL = f"sqlite:///{TESTING_DB_FILE}"


@fixture
async def backend_client() -> AsyncClient:
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """
    # defer import of main to prevent accidentally importing storage too early
    from licensemanager2.backend import main

    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        yield ac


@fixture
async def agent_client() -> AsyncClient:
    """
    A client that can issue fake requests against endpoints in the agent
    """
    # defer import of main to prevent accidentally importing storage too early
    from licensemanager2.agent import main

    async with AsyncClient(app=main.app, base_url="http://test") as ac:
        yield ac


@fixture(scope="session", autouse=True)
def log_sql():
    """
    Set LOG_LEVEL_SQL="DEBUG" to turn on SQL tracing of all tests
    """
    if SETTINGS.LOG_LEVEL_SQL:
        logging.getLogger("sqlalchemy.engine").setLevel(SETTINGS.LOG_LEVEL_SQL)
        logging.getLogger("databases").setLevel(SETTINGS.LOG_LEVEL_SQL)


@fixture(scope="session", autouse=True)
def backend_testing_database():
    """
    Override whatever is set for DATABASE_URL during testing
    """
    # defer import of storage until now, to prevent the database
    # from being initialized implicitly on import
    from licensemanager2.backend.storage import create_all_tables

    create_all_tables()
    yield
    os.remove(TESTING_DB_FILE)


@fixture(autouse=True)
def enforce_testing_database():
    """
    Are you sure we're in a testing database?
    """
    from licensemanager2.backend.storage import database

    assert "-testing" in database.url.database


@fixture(autouse=True)
async def enforce_empty_database():
    """
    Make sure our database is empty at the end of each test
    """
    yield
    from licensemanager2.backend.storage import database

    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 0


@fixture
def ok_response():
    """
    An instance of the OK response
    """
    from licensemanager2.common_response import OK

    return OK()
