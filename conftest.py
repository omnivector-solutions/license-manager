"""
Pytest common fixtures and pytest session configuration
"""
import os

from fastapi.testclient import TestClient
from pytest import fixture

from licensemanager2.backend.settings import SETTINGS


TESTING_DB_FILE = "./sqlite-testing.db"
SETTINGS.DATABASE_URL = f"sqlite:///{TESTING_DB_FILE}"


@fixture
def backend_client():
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """
    # defer import of main to prevent accidentally importing storage too early
    from licensemanager2.backend import main

    return TestClient(main.app)


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


@fixture(scope="function", autouse=True)
def enforce_testing_database():
    """
    Are you sure we're in a testing database?
    """
    from licensemanager2.backend.storage import database

    assert "-testing" in database.url.database


@fixture
async def post_rollback():
    """
    Wrap a transaction around the test that rolls back at the end
    """
    from licensemanager2.backend.storage import database

    async with database.transaction(force_rollback=True) as txn:
        yield txn


@fixture
def ok_response():
    """
    An instance of the OK response
    """
    from licensemanager2.common_response import OK

    return OK()
