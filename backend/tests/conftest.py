import os
import re
from typing import List

import sqlalchemy
from asgi_lifespan import LifespanManager
from httpx import AsyncClient
from pydantic import BaseModel
from pytest import fixture

from lm_backend.api_schemas import LicenseUseReconcile as LUR
from lm_backend.config import settings
from lm_backend.main import app as backend_app
from lm_backend.storage import database


@fixture(scope="session", autouse=True)
def enforce_testing_database():
    match = re.match(r"sqlite:///(.*-testing\.db)", settings.DATABASE_URL)
    if not match:
        raise Exception(f"URL for database is invalid for testing: {settings.DATABASE_URL}")
    testing_db_file = match.group(1)
    yield
    os.remove(testing_db_file)


@fixture(autouse=True)
async def enforce_empty_database():
    """
    Make sure our database is empty at the end of each test
    """
    yield

    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 0


@fixture
def insert_objects():
    """
    A fixture that provides a helper method that perform a database insertion for the
    objects passed as the argument, into the specified table
    """

    async def _helper(objects: List[BaseModel], table: sqlalchemy.Table):
        ModelType = type(objects[0])
        await database.execute_many(query=table.insert(), values=[obj.dict() for obj in objects])
        fetched = await database.fetch_all(table.select())
        return [ModelType.parse_obj(o) for o in fetched]

    return _helper


@fixture(autouse=True)
async def startup_event_force():
    async with LifespanManager(backend_app):
        yield


@fixture
async def backend_client():
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """

    async with AsyncClient(app=backend_app, base_url="http://test") as ac:
        yield ac


@fixture
def some_licenses():
    """
    Some LicenseUse bookings
    """
    inserts = [
        LUR(
            product_feature="hello.world",
            total=100,
            used=19,
            used_licenses=[{"booked": 19, "lead_host": "host1", "user_name": "user1"}],
        ),
        LUR(
            product_feature="hello.dolly",
            total=80,
            used=11,
            used_licenses=[{"booked": 11, "lead_host": "host1", "user_name": "user1"}],
        ),
        LUR(
            product_feature="cool.beans",
            total=11,
            used=11,
            used_licenses=[{"booked": 11, "lead_host": "host1", "user_name": "user1"}],
        ),
    ]
    return inserts
