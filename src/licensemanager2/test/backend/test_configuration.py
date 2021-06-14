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
    assert resp.json() == [ConfigurationRow.parse_obj(x) for x in one_configuration_row]