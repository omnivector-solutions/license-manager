import os
import re

from fastapi.testclient import TestClient
from pytest import fixture
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from lm_simulator.config import settings
from lm_simulator.database import Base
from lm_simulator.main import get_db, subapp
from lm_simulator.schemas import LicenseCreate, LicenseInUseCreate


@fixture(scope="session", autouse=True)
def enforce_testing_database():
    match = re.match(r"sqlite:///(.*-testing\.db)", settings.DATABASE_URL)
    if not match:
        raise Exception(f"URL for database is invalid for testing: {settings.DATABASE_URL}")
    testing_db_file = match.group(1)
    yield
    os.remove(testing_db_file)


@fixture(scope="session")
def engine():
    return create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})


@fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield


@fixture
def session(engine, tables):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, future=True)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@fixture
def client(session):
    def override_get_db():
        yield session

    subapp.dependency_overrides[get_db] = override_get_db
    yield TestClient(subapp)


@fixture
def one_license():
    return LicenseCreate(name="test_name", total=100)


@fixture
def one_license_in_use():
    return LicenseInUseCreate(quantity=10, user_name="user1", lead_host="host1", license_name="test_name")
