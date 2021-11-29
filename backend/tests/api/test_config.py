from typing import List

from httpx import AsyncClient
from pytest import fixture, mark

from lm_backend import table_schemas
from lm_backend.api_schemas import ConfigurationItem, ConfigurationRow
from lm_backend.storage import database


@fixture
def some_configuration_rows() -> List[ConfigurationRow]:
    """
    Some ConfigurationRows
    """
    return [
        ConfigurationRow(
            id=1,
            product="testproduct1",
            features='{"feature1": 1, "feature2": 2, "feature3": 3}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=100,
        ),
        ConfigurationRow(
            id=2,
            product="testproduct2",
            features='{"feature1": 1, "feature2": 2, "feature3": 3}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=200,
        ),
        ConfigurationRow(
            id=3,
            product="testproduct3",
            features='{"feature1": 1, "feature2": 2, "feature3": 3}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=300,
        ),
    ]


@fixture
def some_configuration_items() -> List[ConfigurationItem]:
    """
    Some ConfigurationItems
    """
    return [
        ConfigurationItem(
            id=1,
            product="testproduct1",
            features={"feature1": 1, "feature2": 2, "feature3": 3},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=100,
        ),
        ConfigurationItem(
            id=2,
            product="testproduct2",
            features={"feature1": 1, "feature2": 2, "feature3": 3},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=200,
        ),
        ConfigurationItem(
            id=3,
            product="testproduct3",
            features={"feature1": 1, "feature2": 2, "feature3": 3},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=300,
        ),
    ]


@fixture
def one_configuration_row():
    """
    ConfigurationRow
    """
    return [
        ConfigurationRow(
            id=100,
            product="testproduct1",
            features='{"feature1": 1}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=10000,
        )
    ]


@fixture
def one_configuration_item():
    """
    ConfigurationItem
    """
    return [
        ConfigurationItem(
            id=100,
            product="testproduct1",
            features={"feature1": 1},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=10000,
        )
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_all_configurations(
    backend_client: AsyncClient,
    some_configuration_rows,
    some_configuration_items,
    insert_objects,
):
    """
    Test fetching all configuration rows in the db.
    """
    await insert_objects(some_configuration_rows, table_schemas.config_table)
    resp = await backend_client.get("/lm/api/v1/config/all")
    assert resp.status_code == 200
    assert resp.json() == [ConfigurationItem.parse_obj(x) for x in some_configuration_items]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_configuration(
    backend_client: AsyncClient,
    one_configuration_row,
    one_configuration_item,
    insert_objects,
):
    """
    Test fetching a configuration row.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)
    resp = await backend_client.get("/lm/api/v1/config/100")
    assert resp.status_code == 200
    assert resp.json() == ConfigurationItem.parse_obj(one_configuration_item[0])


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_add_configuration(backend_client: AsyncClient):
    """
    Test adding a configuration row.
    """
    data = {
        "product": "testproduct1",
        "features": '{"feature1": 1, "feature2": 2, "feature3": 3}',
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }

    response = await backend_client.post("/lm/api/v1/config", json=data)
    assert response.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_configuration(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
):
    """
    Test updating a configuration row.
    """
    await insert_objects(one_configuration_row, table_schemas.config_table)
    data = {
        "id": "100",
        "product": "updated_test_product",
        "features": '{"feature1": 1, "feature2": 2, "feature3": 3}',
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }
    resp = await backend_client.put("/lm/api/v1/config/100", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_nonexistant_configuration(backend_client: AsyncClient):
    """
    Test updating a configuration row.
    """
    data = {
        "id": "100000",
        "product": "testproduct1",
        "features": '{"feature1": 1, "feature2": 2, "feature3": 3}',
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }
    resp = await backend_client.put("/lm/api/v1/config/100000", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_configuration(backend_client: AsyncClient, one_configuration_row, insert_objects):
    """
    Test deleting a configuration row.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)
    resp = await backend_client.delete("/lm/api/v1/config/100")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Deleted 100 from the configuration table."


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_nonexistant__configuration(
    backend_client: AsyncClient, one_configuration_row, insert_objects
):
    """
    Attempt to delete a non-existant ID from the database.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)
    resp = await backend_client.delete("/lm/api/v1/config/99999999")
    assert resp.status_code == 404
