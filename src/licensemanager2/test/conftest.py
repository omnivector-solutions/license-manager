"""
Pytest common fixtures and pytest session configuration
"""

import sqlalchemy
from pytest import fixture
from typing import List
from pydantic import BaseModel

from licensemanager2.backend.storage import database
from licensemanager2.backend.configuration import ConfigurationRow


@fixture(scope="session", autouse=True)
def some_configuration_rows() -> List[ConfigurationRow]:
    """
    Some ConfigurationRows
    """
    return [
        ConfigurationRow(
            id=1,
            product="testproduct1",
            features=["feature1", "feature2", "feature3"],
            license_servers=["licenseserver1"],
            license_server_type="servertype1",
            grace_time=100,
        ),
        ConfigurationRow(
            id=2,
            product="testproduct2",
            features=["feature1", "feature2", "feature3"],
            license_servers=["licenseserver2"],
            license_server_type="servertype2",
            grace_time=200,
        ),
        ConfigurationRow(
            id=3,
            product="testproduct3",
            features=["feature1", "feature2", "feature3"],
            license_servers=["licenseserver3"],
            license_server_type="servertype3",
            grace_time=300,
        ),
    ]


@fixture(scope="session", autouse=True)
def one_configuration_row():
    """
    ConfigurationRows
    """
    return [ConfigurationRow(
        id=100,
        product="testproduct100",
        features=["feature1", "feature2", "feature3"],
        license_servers=["licenseserver100"],
        license_server_type="servertype100",
        grace_time=10000,
    )]


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