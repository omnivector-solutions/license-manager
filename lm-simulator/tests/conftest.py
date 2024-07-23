import asyncio
from typing import List

from httpx import AsyncClient
from pytest import fixture
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from yarl import URL

from lm_simulator.config import settings
from lm_simulator.database import Base, get_session
from lm_simulator.main import subapp
from lm_simulator.models import License, LicenseInUse
from lm_simulator.schemas import LicenseCreate, LicenseInUseCreate


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


@fixture(autouse=True, scope="session")
async def engine():
    """
    Provide a fixture to prepare the test database.
    """
    engine = create_async_engine(
        str(
            URL.build(
                scheme="postgresql+asyncpg",
                user=settings.TEST_DATABASE_USER,
                password=settings.TEST_DATABASE_PSWD,
                host=settings.TEST_DATABASE_HOST,
                port=settings.TEST_DATABASE_PORT,
                path=f"/{settings.TEST_DATABASE_NAME}",
            )
        )
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@fixture(scope="function")
async def synth_session(engine):
    async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session_maker() as session:
        await session.begin_nested()
        yield session
        await session.rollback()
        await session.close()


@fixture
async def backend_client(synth_session):
    def override_get_session():
        yield synth_session

    subapp.dependency_overrides[get_session] = override_get_session
    async with AsyncClient(app=subapp, base_url="http://test") as client:
        yield client


@fixture
def insert_objects(synth_session):
    """
    Fixture to insert objects into the database.
    """

    async def _helper(
        objects: List[Base],
        table: Base,
    ):
        db_objects = [table(**obj.model_dump()) for obj in objects]

        for obj in db_objects:
            synth_session.add(obj)

        await synth_session.flush()

        await asyncio.gather(synth_session.refresh(obj) for obj in db_objects if obj)
        return db_objects

    return _helper


@fixture
def read_objects(synth_session):
    """
    Fixture to read objects from the database.
    """

    async def _helper(stmt):
        fetched = (await synth_session.execute(stmt)).scalars().all()

        await asyncio.gather(synth_session.refresh(obj) for obj in fetched if obj)
        return fetched

    return _helper


@fixture
def read_object(synth_session):
    """
    Fixture to read a single object from the database.
    """

    async def _helper(stmt):
        fetched = (await synth_session.execute(stmt)).scalar()

        await synth_session.refresh(fetched)
        return fetched

    return _helper


@fixture
def delete_objects(synth_session):
    """
    Fixture to delete objects from the database.
    """

    async def _helper(object):
        await synth_session.delete(object)
        await synth_session.flush()

    return _helper


@fixture
def one_license():
    return LicenseCreate(name="test_license", total=1000)


@fixture
def licenses():
    return [
        LicenseCreate(name="test_license1", total=1000),
        LicenseCreate(name="test_license2", total=2000),
    ]


@fixture
def one_license_in_use():
    return LicenseInUseCreate(quantity=100, user_name="user1", lead_host="host1", license_name="test_license")


@fixture
def one_license_in_use__not_enough():
    return LicenseInUseCreate(
        quantity=1500, user_name="user1", lead_host="host1", license_name="test_license"
    )


@fixture
def one_license_in_use__not_found():
    return LicenseInUseCreate(quantity=100, user_name="user1", lead_host="host1", license_name="not_found")


@fixture
def licenses_in_use():
    return [
        LicenseInUseCreate(quantity=100, user_name="user1", lead_host="host1", license_name="test_license1"),
        LicenseInUseCreate(quantity=200, user_name="user2", lead_host="host2", license_name="test_license2"),
    ]
