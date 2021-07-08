"""
Configuration of pytest for backend tests
"""
from typing import List

from httpx import AsyncClient
from pydantic import BaseModel
from pytest import fixture
import sqlalchemy

from licensemanager2.backend.license import LicenseUseReconcile as LUR
from licensemanager2.backend.storage import database


async def insert_objects(objects: List[BaseModel], table: sqlalchemy.Table):
    """
    Perform a database insertion for the objects passed as the argument, into
    the specified table
    """
    ModelType = type(objects[0])
    await database.execute_many(
        query=table.insert(), values=[obj.dict() for obj in objects]
    )
    fetched = await database.fetch_all(table.select())
    return [ModelType.parse_obj(o) for o in fetched]


@fixture
async def backend_client():
    """
    A client that can issue fake requests against fastapi endpoint functions in the backend
    """
    # defer import of main to prevent accidentally importing storage too early
    from licensemanager2.backend.main import app as backend_app

    async with AsyncClient(app=backend_app, base_url="http://test") as ac:
        yield ac


@fixture
def some_licenses():
    """
    Some LicenseUse bookings
    """
    inserts = [
        LUR(
            id=1,
            product_feature="hello.world",
            total=100,
            used=19,
        ),
        LUR(
            id=2,
            product_feature="hello.dolly",
            total=80,
            used=11,
        ),
        LUR(
            id=3,
            product_feature="cool.beans",
            total=11,
            used=11,
        ),
    ]
    return inserts
