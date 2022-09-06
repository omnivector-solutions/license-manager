import contextlib
import dataclasses
import datetime
import os
import re
import typing

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

    async def _helper(objects: typing.List[BaseModel], table: sqlalchemy.Table):
        ModelType = type(objects[0])
        await database.execute_many(
            query=table.insert(),
            values=[obj.dict(exclude_unset=True) for obj in objects],
        )
        fetched = await database.fetch_all(table.select())
        return [ModelType.parse_obj(o) for o in fetched]

    return _helper


@fixture(autouse=True)
async def startup_event_force():
    async with LifespanManager(backend_app):
        yield


@fixture(autouse=True)
def enforce_mocked_oidc_provider(mock_openid_server):
    """
    Enforce that the OIDC provider used by armada-security is the mock_openid_server provided as a fixture.
    No actual calls to an OIDC provider will be made.
    """
    yield


@fixture
async def inject_security_header(backend_client, build_rs256_token):
    """
    Provides a helper method that will inject a security token into the requests for a test client. If no
    permisions are provided, the security token will still be valid but will not carry any permissions. Uses
    the `build_rs256_token()` fixture from the armasec package.
    """

    def _helper(owner_id: str, *permissions: typing.List[str]):
        token = build_rs256_token(claim_overrides=dict(sub=owner_id, permissions=permissions))
        backend_client.headers.update({"Authorization": f"Bearer {token}"})

    return _helper


@fixture
async def inject_client_id_in_security_header(backend_client, build_rs256_token):
    """
    Provides a helper method that will inject a security token into the requests for a test client. If no
    client_id is provided, the security token will still be valid but will not carry any identification
    in the `azp` parameter. Uses the `build_rs256_token()` fixture from the armasec package.
    """

    def _helper(client_id: str, *permissions: typing.List[str]):
        token = build_rs256_token(claim_overrides=dict(azp=client_id, permissions=permissions))
        backend_client.headers.update({"Authorization": f"Bearer {token}"})

    return _helper


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


@fixture
def time_frame():
    """
    Provides a fixture to use as a context manager where an event can be checked to have happened during the
    time-frame of the context manager.
    """

    @dataclasses.dataclass
    class TimeFrame:
        """
        Class for storing the beginning and end of a time frame."
        """

        now: datetime.datetime
        later: typing.Optional[datetime.datetime]

        def __contains__(self, moment: datetime.datetime):
            """
            Checks if a given moment falls within a time-frame.
            """
            if self.later is None:
                return False
            return moment >= self.now and moment <= self.later

    @contextlib.contextmanager
    def _helper():
        """
        Context manager for defining the time-frame for the time_frame fixture.
        """
        window = TimeFrame(now=datetime.datetime.utcnow().replace(microsecond=0), later=None)
        yield window
        window.later = datetime.datetime.utcnow() + datetime.timedelta(seconds=1)

    return _helper
