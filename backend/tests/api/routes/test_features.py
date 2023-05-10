from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models import Feature
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_configuration,
    create_one_product,
    clean_up_database,
):
    """
    Test adding a Feature.
    """
    configuration_id = create_one_configuration[0].id
    product_id = create_one_product[0].id

    data = {"name": "abaqus", "product_id": product_id, "config_id": configuration_id, "reserved": 0}

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.post("/lm/features", json=data)
    assert response.status_code == 201

    stmt = select(Feature).where(Feature.name == data["name"])
    fetched = await read_object(stmt)

    assert fetched.name == data["name"]
    assert fetched.config_id == configuration_id
    assert fetched.product_id == product_id
    assert fetched.reserved == data["reserved"]


@mark.asyncio
async def test_get_all_features__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_features,
    clean_up_database,
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
    clean_up_database,
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
    clean_up_database,
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
    clean_up_database,
):
    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_VIEW)
    response = await backend_client.get(f"/lm/features/{id}")

    assert response.status_code == 200

    response_feature = response.json()
    assert response_feature["name"] == create_one_feature[0].name
    assert response_feature["reserved"] == create_one_feature[0].reserved


@mark.asyncio
async def test_update_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    read_object,
    clean_up_database,
):
    new_feature = {"name": "abaqus_2"}

    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.put(f"/lm/features/{id}", json=new_feature)

    assert response.status_code == 200

    stmt = select(Feature).where(Feature.id == id)
    fetch_feature = await read_object(stmt)

    assert fetch_feature.name == new_feature["name"]


@mark.asyncio
async def test_delete_feature__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_feature,
    read_object,
    clean_up_database,
):
    id = create_one_feature[0].id

    inject_security_header("owner1", Permissions.FEATURE_EDIT)
    response = await backend_client.delete(f"/lm/features/{id}")

    assert response.status_code == 200
    stmt = select(Feature).where(Feature.id == id)
    fetch_feature = await read_object(stmt)

    assert fetch_feature is None
