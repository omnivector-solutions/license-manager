import asyncio
import contextlib
import dataclasses
import datetime
import typing
from unittest.mock import patch

import sqlalchemy
import sqlalchemy.orm
from httpx import ASGITransport, AsyncClient
from pytest import fixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from lm_api.api.models.crud_base import CrudBase
from lm_api.config import settings
from lm_api.database import engine_factory


@fixture(scope="session")
def event_loop():
    """
    Create an instance of the default event loop for each test case.

    This fixture is used to run each test in a different async loop. Running all
    in the same loop causes errors with SQLAlchemy. See the following two issues:

    1. https://github.com/tiangolo/fastapi/issues/5692
    2. https://github.com/encode/starlette/issues/1315

    [Reference](https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html)
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@fixture
async def test_app():
    """
    A test app to be used by the test backend_client.
    """
    from lm_api.main import app as test_app

    yield test_app


@fixture
async def backend_client(test_app):
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """
    async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as ac:
        yield ac


@fixture(autouse=True)
async def synth_engine():
    """
    Provide a fixture to prepare the test database.
    """
    engine = engine_factory.get_engine()
    async with engine.begin() as connection:
        await connection.run_sync(CrudBase.metadata.create_all, checkfirst=True)
    try:
        yield engine
    finally:
        async with engine.begin() as connection:
            await connection.run_sync(CrudBase.metadata.drop_all)
        await engine_factory.cleanup()


@fixture(scope="function")
async def synth_session():
    """
    Get a session from the engine_factory for the current test function.

    This is necessary to make sure that the test code uses the same session as the one returned by
    the dependency injection for the router code. Otherwise, changes made in the router's session would not
    be visible in the test code. Not that changes made in this synthesized session are always rolled back
    and never committed.
    """
    session = engine_factory.get_session()
    with patch("lm_api.database.engine_factory.get_session", return_value=session):
        await session.begin_nested()
        yield session
        await session.rollback()
        await session.close()


@fixture
def insert_objects(synth_session: AsyncSession):
    """
    A fixture that provides a helper method that perform a database insertion for the
    objects passed as the argument, into the specified table
    """

    async def _helper(
        objects: typing.List[sqlalchemy.Table],
        table: sqlalchemy.Table,
        subquery_relation: InstrumentedAttribute = None,
    ):
        db_objects = [table(**obj) for obj in objects]
        for obj in db_objects:
            synth_session.add(obj)
        await synth_session.flush()
        query = sqlalchemy.select(table)
        if subquery_relation is not None:
            query = query.options(sqlalchemy.orm.subqueryload(subquery_relation))
        fetched = (await synth_session.execute(query)).scalars().all()
        return [obj for obj in fetched]

    return _helper


@fixture
async def update_object(synth_session: AsyncSession):
    """
    A fixture that provides a helper method that perform a database update
    for the object passed as the argument, into the specified table
    """

    async def _helper(
        object: typing.List[sqlalchemy.Table],
        id: int,
        table: sqlalchemy.Table,
        subquery_relation: InstrumentedAttribute = None,
    ):
        query = await synth_session.execute(select(table).filter(table.id == id))
        db_obj = query.scalar_one_or_none()

        for field, value in object:
            if value is not None:
                setattr(db_obj, field, value)
        await synth_session.flush()
        await synth_session.refresh(db_obj)
        return db_obj

    return _helper


@fixture
def read_objects(synth_session: AsyncSession):
    """
    A fixture that provides a helper method that perform a database
    read all operation using the specified statement.
    """

    async def _helper(
        stmt,
    ):
        fetched = (await synth_session.execute(stmt)).scalars().all()

        # Necessary to lazy load relationships for joined models
        await asyncio.gather(synth_session.refresh(obj) for obj in fetched if obj is not None)
        return fetched

    return _helper


@fixture
def read_object(synth_session: AsyncSession):
    """
    A fixture that provides a helper method that perform a database
    read operation using the specified statement.
    """

    async def _helper(
        stmt,
    ):
        fetched = (await synth_session.execute(stmt)).scalars().one_or_none()

        # Necessary to lazy load relationships for joined models
        if fetched is not None:
            await synth_session.refresh(fetched)
        return fetched

    return _helper


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
    permissions are provided, the security token will still be valid but will not carry any permissions. Uses
    the `build_rs256_token()` fixture from the armasec package.
    """

    def _helper(
        owner_email: str,
        *permissions: typing.List[str],
        client_id: typing.Optional[str] = None,
        organization_id: typing.Optional[str] = None,
    ):
        claim_overrides = dict(
            email=owner_email,
            client_id=client_id,
            permissions=permissions,
            organization={organization_id: dict()},
        )
        token = build_rs256_token(claim_overrides=claim_overrides)
        backend_client.headers.update({"Authorization": f"Bearer {token}"})

    return _helper


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


@fixture
def tweak_settings():
    """
    Provide a fixture to use as a context manager where the app settings may be temporarily changed.
    """

    @contextlib.contextmanager
    def _helper(**kwargs):
        """
        Context manager for tweaking app settings temporarily.
        """
        previous_values = {}
        for key, value in kwargs.items():
            previous_values[key] = getattr(settings, key)
            setattr(settings, key, value)
        yield
        for key, value in previous_values.items():
            setattr(settings, key, value)

    return _helper
