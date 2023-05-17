import asyncio
import contextlib
import dataclasses
import datetime
import typing

import sqlalchemy
import sqlalchemy.orm
from httpx import AsyncClient
from pytest import fixture
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import InstrumentedAttribute

from lm_backend.api.models.booking import Booking
from lm_backend.api.models.cluster import Cluster
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.models.inventory import Inventory
from lm_backend.api.models.job import Job
from lm_backend.api.models.license_server import LicenseServer
from lm_backend.api.models.product import Product
from lm_backend.session import AsyncScopedSession


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

    from lm_backend.main import app as test_app

    yield test_app


@fixture
async def backend_client(test_app):
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """

    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@fixture
def get_session() -> typing.Callable[[None], typing.AsyncGenerator[AsyncSession, None]]:
    """A fixture to return the async session used to run SQL queries against a database."""

    @contextlib.asynccontextmanager
    async def _get_session() -> typing.AsyncGenerator[AsyncSession, None]:
        """Get the async session to execute queries against the database."""
        async with AsyncScopedSession() as session:
            async with session.begin():
                try:
                    yield session
                except Exception as err:
                    await session.rollback()
                    raise err
                finally:
                    await session.close()

    return _get_session


@fixture
def insert_objects(get_session: typing.AsyncGenerator[AsyncSession, None]):
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
        async with get_session() as sess:
            for obj in db_objects:
                sess.add(obj)
            await sess.commit()
        async with get_session() as sess:
            query = sqlalchemy.select(table)
            if subquery_relation is not None:
                query = query.options(sqlalchemy.orm.subqueryload(subquery_relation))
            fetched = (await sess.execute(query)).scalars().all()
        return [obj for obj in fetched]

    return _helper


@fixture
async def update_object(get_session: typing.AsyncGenerator[AsyncSession, None]):
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
        async with get_session() as sess:
            query = await sess.execute(select(table).filter(table.id == id))
            db_obj = query.scalar_one_or_none()

            for field, value in object:
                if value is not None:
                    setattr(db_obj, field, value)
            await sess.flush()
        await sess.refresh(db_obj)
        return db_obj

    return _helper


@fixture
def read_objects(get_session: typing.AsyncGenerator[AsyncSession, None]):
    """
    A fixture that provides a helper method that perform a database
    read all operation using the specified statement.
    """

    async def _helper(
        stmt,
    ):
        async with get_session() as sess:
            fetched = (await sess.execute(stmt)).scalars().all()
        return [obj for obj in fetched]

    return _helper


@fixture
def read_object(get_session: typing.AsyncGenerator[AsyncSession, None]):
    """
    A fixture that provides a helper method that perform a database
    read operation using the specified statement.
    """

    async def _helper(
        stmt,
    ):
        async with get_session() as sess:
            return (await sess.execute(stmt)).scalars().one_or_none()

    return _helper


@fixture(autouse=True)
async def clean_up_database(get_session: typing.AsyncGenerator[AsyncSession, None]) -> None:
    """Clean up the database after test run."""
    yield
    async with get_session() as sess:
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Booking.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Job.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Inventory.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Feature.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Product.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {LicenseServer.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Configuration.__tablename__};"""))
        await sess.execute(sqlalchemy.text(f"""DELETE FROM {Cluster.__tablename__};"""))
        await sess.commit()


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
