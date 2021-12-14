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
            name="Product 1: Features 1, 2, 3",
            product="testproduct1",
            features='{"feature1": 1, "feature2": 2, "feature3": 3}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=100,
        ),
        ConfigurationRow(
            id=2,
            name="Product 2: Features 1, 2, 3",
            product="testproduct2",
            features='{"feature1": 1, "feature2": 2, "feature3": 3}',
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=200,
        ),
        ConfigurationRow(
            id=3,
            name="Product 3: Features 1, 2, 3",
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
            name="Product 1: Features 1, 2, 3",
            product="testproduct1",
            features={"feature1": 1, "feature2": 2, "feature3": 3},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=100,
        ),
        ConfigurationItem(
            id=2,
            name="Product 2: Features 1, 2, 3",
            product="testproduct2",
            features={"feature1": 1, "feature2": 2, "feature3": 3},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=200,
        ),
        ConfigurationItem(
            id=3,
            name="Product 3: Features 1, 2, 3",
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
            name="Product 1: Feature 1",
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
            name="Product 1: Feature 1",
            product="testproduct1",
            features={"feature1": 1},
            license_servers=["flexlm:127.0.0.1:2345"],
            license_server_type="flexlm",
            grace_time=10000,
        )
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_all_configurations__success(
    backend_client: AsyncClient,
    some_configuration_rows,
    some_configuration_items,
    insert_objects,
    inject_security_header,
):
    """
    Test fetching all configuration rows in the db.
    """
    await insert_objects(some_configuration_rows, table_schemas.config_table)

    inject_security_header("owner1", "license-manager:config:read")
    resp = await backend_client.get("/lm/api/v1/config/all")

    assert resp.status_code == 200
    assert resp.json() == [ConfigurationItem.parse_obj(x) for x in some_configuration_items]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_all_configurations__fails_with_invalid_permissions(
    backend_client: AsyncClient,
    some_configuration_rows,
    some_configuration_items,
    insert_objects,
    inject_security_header,
):
    """
    Test that 401 or 403 are returned when permissions are missing or invalid.
    """
    await insert_objects(some_configuration_rows, table_schemas.config_table)

    # No permission
    resp = await backend_client.get("/lm/api/v1/config/all")
    assert resp.status_code == 401

    # Bad permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/config/all")
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_configuration__success(
    backend_client: AsyncClient,
    one_configuration_row,
    one_configuration_item,
    insert_objects,
    inject_security_header,
):
    """
    Test fetching a configuration row.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)

    inject_security_header("owner1", "license-manager:config:read")
    resp = await backend_client.get("/lm/api/v1/config/100")

    assert resp.status_code == 200
    assert resp.json() == ConfigurationItem.parse_obj(one_configuration_item[0])


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_configuration__fail_on_bad_permission(
    backend_client: AsyncClient,
    one_configuration_row,
    one_configuration_item,
    insert_objects,
    inject_security_header,
):
    """
    Test fetching a configuration row.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)

    # No Permission
    resp = await backend_client.get("/lm/api/v1/config/100")
    assert resp.status_code == 401

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/config/100")
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_add_configuration__success(
    backend_client: AsyncClient,
    inject_security_header,
):
    """
    Test adding a configuration row.
    """
    data = {
        "name": "Product 1: Features 1, 2, 3",
        "product": "testproduct1",
        "features": '{"feature1": 1, "feature2": 2, "feature3": 3}',
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }

    inject_security_header("owner1", "license-manager:config:write")
    response = await backend_client.post("/lm/api/v1/config", json=data)
    assert response.status_code == 200

    query = table_schemas.config_table.select().where(
        table_schemas.config_table.c.name == "Product 1: Features 1, 2, 3"
    )
    fetched = await database.fetch_one(query)
    assert fetched.product == "testproduct1"
    assert fetched.features == '{"feature1": 1, "feature2": 2, "feature3": 3}'
    assert fetched.license_servers == ["licenseserver100"]
    assert fetched.license_server_type == "servertype100"
    assert fetched.grace_time == 10000


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_add_configuration__fail_on_bad_permission(
    backend_client: AsyncClient,
    inject_security_header,
):
    """
    Test request returns a 401 or 403 if permissions are missing or invalid.
    """
    data = {
        "product": "testproduct1",
        "features": '{"feature1": 1, "feature2": 2, "feature3": 3}',
        "license_servers": ["licenseserver100"],
        "license_server_type": "servertype100",
        "grace_time": "10000",
    }

    # No Permission
    response = await backend_client.post("/lm/api/v1/config", json=data)
    assert response.status_code == 401

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    response = await backend_client.post("/lm/api/v1/config", json=data)
    assert response.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_configuration__success(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
    inject_security_header,
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
    inject_security_header("owner1", "license-manager:config:write")
    resp = await backend_client.put("/lm/api/v1/config/100", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_configuration__fail_on_bad_permission(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
    inject_security_header,
):
    """
    Test request returns a 401 or 403 if permissions are missing or invalid.
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

    # No Permission
    resp = await backend_client.put("/lm/api/v1/config/100", json=data)
    assert resp.status_code == 401

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.put("/lm/api/v1/config/100", json=data)
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_update_nonexistant_configuration(
    backend_client: AsyncClient,
    inject_security_header,
):
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

    inject_security_header("owner1", "license-manager:config:write")
    resp = await backend_client.put("/lm/api/v1/config/100000", json=data)
    assert resp.status_code == 200


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_configuration__success(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
    inject_security_header,
):
    """
    Test deleting a configuration row.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)

    inject_security_header("owner1", "license-manager:config:write")
    resp = await backend_client.delete("/lm/api/v1/config/100")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Deleted 100 from the configuration table."


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_configuration__fail_on_bad_permission(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
    inject_security_header,
):
    """
    Test request returns a 401 or 403 if permissions are missing or invalid.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)

    # Missing Permission
    resp = await backend_client.delete("/lm/api/v1/config/100")
    assert resp.status_code == 401

    # Invalid Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.delete("/lm/api/v1/config/100")
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_nonexistant__configuration(
    backend_client: AsyncClient,
    one_configuration_row,
    insert_objects,
    inject_security_header,
):
    """
    Attempt to delete a non-existant ID from the database.
    """

    await insert_objects(one_configuration_row, table_schemas.config_table)
    inject_security_header("owner1", "license-manager:config:write")
    resp = await backend_client.delete("/lm/api/v1/config/99999999")
    assert resp.status_code == 404
