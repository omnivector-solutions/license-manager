from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.feature import Feature
from lm_backend.api.models.inventory import Inventory
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_configuration,
    create_one_product,
):
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    data = {"name": "abaqus", "product_id": product_id, "config_id": configuration_id, "reserved": 0}

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.post("/lm/features", json=data)
    assert response.status_code == 201

    stmt = select(Feature).where(Feature.name == data["name"])
    feature_fetched = await read_object(stmt)

    assert feature_fetched.name == data["name"]
    assert feature_fetched.config_id == configuration_id
    assert feature_fetched.product_id == product_id
    assert feature_fetched.reserved == data["reserved"]

    stmt = select(Inventory).where(Inventory.feature_id == feature_fetched.id)
    inventory_fetched = await read_object(stmt)

    assert inventory_fetched.feature_id == feature_fetched.id


@mark.asyncio
async def test_get_all_features__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_features,
):
    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get("/lm/features")

    assert response.status_code == 200

    response_features = response.json()
    assert response_features[0]["name"] == create_features[0].name
    assert response_features[0]["reserved"] == create_features[0].reserved

    assert response_features[1]["name"] == create_features[1].name
    assert response_features[1]["reserved"] == create_features[1].reserved


@mark.asyncio
async def test_get_all_features__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_features,
):
    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get(f"/lm/features/?search={create_features[0].name}")

    assert response.status_code == 200

    response_features = response.json()
    assert response_features[0]["name"] == create_features[0].name
    assert response_features[0]["reserved"] == create_features[0].reserved


@mark.asyncio
async def test_get_all_features__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_features,
):
    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get("/lm/features/?sort_field=name&sort_ascending=false")

    assert response.status_code == 200

    response_features = response.json()
    assert response_features[0]["name"] == create_features[1].name
    assert response_features[0]["reserved"] == create_features[1].reserved

    assert response_features[1]["name"] == create_features[0].name
    assert response_features[1]["reserved"] == create_features[0].reserved


@mark.asyncio
async def test_get_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
):
    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get(f"/lm/features/{id}")

    assert response.status_code == 200

    response_feature = response.json()
    assert response_feature["name"] == create_one_feature[0].name
    assert response_feature["reserved"] == create_one_feature[0].reserved


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_feature__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    id,
):
    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get(f"/lm/features/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_update_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    read_object,
):
    new_feature = {"name": "abaqus_2"}

    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{id}", json=new_feature)

    assert response.status_code == 200

    stmt = select(Feature).where(Feature.id == id)
    fetch_feature = await read_object(stmt)

    assert fetch_feature.name == new_feature["name"]


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_update_feature__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    id,
):
    new_feature = {"name": "abaqus_2"}

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{id}", json=new_feature)

    assert response.status_code == 404


@mark.asyncio
async def test_update_feature__fail_with_bad_data(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
):
    new_feature = {"bla": "bla"}

    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{id}", json=new_feature)

    assert response.status_code == 400


@mark.asyncio
async def test_update_inventory__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    create_one_inventory,
    read_object,
    read_objects,
    synth_session,
):
    new_inventory = {"total": 9999, "used": 9}

    feature_id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{feature_id}/update_inventory", json=new_inventory)

    assert response.status_code == 200

    stmt = select(Feature).where(Feature.id == feature_id)
    fetch_feature = await read_object(stmt)

    assert fetch_feature.inventory.total == new_inventory["total"]
    assert fetch_feature.inventory.used == new_inventory["used"]


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_update_inventory__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    create_one_inventory,
    read_object,
    id,
):
    new_inventory = {"total": 9999, "used": 9}

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{id}/update_inventory", json=new_inventory)

    assert response.status_code == 404


@mark.asyncio
async def test_update_inventory__fail_with_bad_data(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    create_one_inventory,
):
    new_inventory = {"bla": "bla"}

    feature_id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{feature_id}/update_inventory", json=new_inventory)

    assert response.status_code == 400


@mark.asyncio
async def test_delete_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    read_object,
):
    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.delete(f"/lm/features/{id}")

    assert response.status_code == 200
    stmt = select(Feature).where(Feature.id == id)
    fetch_feature = await read_object(stmt)

    assert fetch_feature is None


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_delete_feature__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    id,
):
    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.delete(f"/lm/features/{id}")

    assert response.status_code == 404
