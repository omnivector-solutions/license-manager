"""
Tests of the /config API endpoints
"""
from httpx import AsyncClient
from pytest import mark

from licensemanager2.backend import schema
from licensemanager2.backend.configuration import ConfigurationRow
from licensemanager2.backend.storage import database
from licensemanager2.test.conftest import insert_objects


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_all_configurations(
    backend_client: AsyncClient, some_configuration_rows
):
    """
    Test fetching all configuration rows in the db.
    """
    await insert_objects(some_configuration_rows, schema.config_table)
    resp = await backend_client.get("/api/v1/config/all")
    assert resp.status_code == 200
    assert resp.json() == [ConfigurationRow.parse_obj(x) for x in some_configuration_rows]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_configuration(
    backend_client: AsyncClient, one_configuration_row
):
    """
    Test fetching a configuration row.
    """

    await insert_objects(one_configuration_row, schema.config_table)
    resp = await backend_client.get("/api/v1/config/100")
    assert resp.status_code == 200
    assert resp.json() == [ConfigurationRow.parse_obj(one_configuration_row[0])]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_add_configuration(
    backend_client: AsyncClient, one_configuration_row
):
    """
    Test adding a configuration row.
    """
    data = {
        "id": "100",
        "product": "testproduct1",
        "features": ["feature1", "feature2", "feature3"],
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }

    response = await backend_client.post("/api/v1/config", json=data)
    assert response.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_configuration(
    backend_client: AsyncClient, one_configuration_row
):
    """
    Test updating a configuration row.
    """
    await insert_objects(one_configuration_row, schema.config_table)
    data = {
        "id": "100",
        "product": "updated_test_product",
        "features": ["feature1", "feature2", "feature3"],
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }
    resp = await backend_client.put("/api/v1/config/100", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_nonexistant_configuration(
    backend_client: AsyncClient,
):
    """
    Test updating a configuration row.
    """
    data = {
        "id": "100000",
        "product": "testproduct1",
        "features": ["feature1", "feature2", "feature3"],
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }
    resp = await backend_client.put("/api/v1/config/100000", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_configuration(
    backend_client: AsyncClient, one_configuration_row
):
    """
    Test deleting a configuration row.
    """

    await insert_objects(one_configuration_row, schema.config_table)
    resp = await backend_client.delete("/api/v1/config/100")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Deleted 100 from the configuration table."


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_nonexistant__configuration(
    backend_client: AsyncClient, one_configuration_row
):
    """
    Attempt to delete a non-existant ID from the database.
    """

    await insert_objects(one_configuration_row, schema.config_table)
    resp = await backend_client.delete("/api/v1/config/99999999")
    assert resp.status_code == 400