from httpx import AsyncClient
from pytest import fixture, mark
from sqlalchemy import select

from lm_backend.api.models import Inventory
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_inventory__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_feature,
    clean_up_database,
):
    """
    Test adding an Inventory.
    """
    feature_id = create_one_feature[0].id

    data = {
        "feature_id": feature_id,
        "total": 1000,
        "used": 350,
    }

    inject_security_header("owner1", Permissions.INVENTORY_EDIT)
    response = await backend_client.post("/lm/inventories", json=data)

    assert response.status_code == 201

    stmt = select(Inventory).where(Inventory.feature_id == data["feature_id"])
    fetched = await read_object(stmt)

    assert fetched.feature_id == data["feature_id"]
    assert fetched.total == data["total"]
    assert fetched.used == data["used"]


@mark.asyncio
async def test_get_all_inventories__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_inventories,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.INVENTORY_VIEW)
    response = await backend_client.get("/lm/inventories")

    assert response.status_code == 200

    response_inventories = response.json()
    assert response_inventories[0]["feature_id"] == create_inventories[0].feature_id
    assert response_inventories[0]["total"] == create_inventories[0].total
    assert response_inventories[0]["used"] == create_inventories[0].used

    assert response_inventories[1]["feature_id"] == create_inventories[1].feature_id
    assert response_inventories[1]["total"] == create_inventories[1].total
    assert response_inventories[1]["used"] == create_inventories[1].used


@mark.asyncio
async def test_get_inventory__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_inventory,
    clean_up_database,
):
    id = create_one_inventory[0].id

    inject_security_header("owner1", Permissions.INVENTORY_VIEW)
    response = await backend_client.get(f"/lm/inventories/{id}")

    assert response.status_code == 200

    response_inventory = response.json()
    assert response_inventory["feature_id"] == create_one_inventory[0].feature_id
    assert response_inventory["total"] == create_one_inventory[0].total
    assert response_inventory["used"] == create_one_inventory[0].used


@mark.asyncio
async def test_delete_inventory__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_inventory,
    read_object,
    clean_up_database,
):
    id = create_one_inventory[0].id

    inject_security_header("owner1", Permissions.INVENTORY_EDIT)
    response = await backend_client.delete(f"/lm/inventories/{id}")

    assert response.status_code == 200
    stmt = select(Inventory).where(Inventory.id == id)
    fetch_inventory = await read_object(stmt)

    assert fetch_inventory is None
