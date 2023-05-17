from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.configuration import Configuration
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_configuration__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_cluster,
    clean_up_database,
):
    cluster_id = create_one_cluster[0].id

    data = {
        "name": "Abaqus",
        "cluster_id": cluster_id,
        "grace_time": 60,
    }

    inject_security_header("owner1", Permissions.CONFIG_EDIT)
    response = await backend_client.post("/lm/configurations", json=data)
    assert response.status_code == 201

    stmt = select(Configuration).where(Configuration.name == "Abaqus")
    fetched = await read_object(stmt)

    assert fetched.name == "Abaqus"


@mark.asyncio
async def test_get_all_configurations__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.CONFIG_VIEW)
    response = await backend_client.get("/lm/configurations")

    assert response.status_code == 200

    response_configurations = response.json()
    assert response_configurations[0]["name"] == create_configurations[0].name
    assert response_configurations[0]["cluster_id"] == create_configurations[0].cluster_id
    assert response_configurations[0]["grace_time"] == create_configurations[0].grace_time

    assert response_configurations[1]["name"] == create_configurations[1].name
    assert response_configurations[1]["cluster_id"] == create_configurations[1].cluster_id
    assert response_configurations[1]["grace_time"] == create_configurations[1].grace_time


@mark.asyncio
async def test_get_all_configurations__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.CONFIG_VIEW)
    response = await backend_client.get(f"/lm/configurations/?search={create_configurations[0].name}")

    assert response.status_code == 200

    response_configuration = response.json()
    assert response_configuration[0]["name"] == create_configurations[0].name
    assert response_configuration[0]["cluster_id"] == create_configurations[0].cluster_id
    assert response_configuration[0]["grace_time"] == create_configurations[0].grace_time


@mark.asyncio
async def test_get_all_configurations__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_configurations,
    clean_up_database,
):

    inject_security_header("owner1", Permissions.CONFIG_VIEW)
    response = await backend_client.get("/lm/configurations/?sort_field=name&sort_ascending=false")

    assert response.status_code == 200

    response_clusters = response.json()
    assert response_clusters[0]["name"] == create_configurations[1].name
    assert response_clusters[0]["cluster_id"] == create_configurations[1].cluster_id
    assert response_clusters[0]["grace_time"] == create_configurations[1].grace_time

    assert response_clusters[1]["name"] == create_configurations[0].name
    assert response_clusters[1]["cluster_id"] == create_configurations[0].cluster_id
    assert response_clusters[1]["grace_time"] == create_configurations[0].grace_time


@mark.asyncio
async def test_get_configuration__success(
    backend_client: AsyncClient,
    inject_security_header,
    insert_objects,
    create_one_configuration,
    clean_up_database,
):
    id = create_one_configuration[0].id

    inject_security_header("owner1", Permissions.CONFIG_VIEW)
    response = await backend_client.get(f"/lm/configurations/{id}")

    assert response.status_code == 200

    response_configuration = response.json()
    assert response_configuration["name"] == create_one_configuration[0].name
    assert response_configuration["cluster_id"] == create_one_configuration[0].cluster_id
    assert response_configuration["grace_time"] == create_one_configuration[0].grace_time


@mark.asyncio
async def test_update_configuration__success(
    backend_client: AsyncClient,
    inject_security_header,
    insert_objects,
    create_one_configuration,
    read_object,
    clean_up_database,
):
    new_configuration = {
        "name": "New Abaqus",
    }

    id = create_one_configuration[0].id

    inject_security_header("owner1", Permissions.CONFIG_EDIT)
    response = await backend_client.put(f"/lm/configurations/{id}", json=new_configuration)

    assert response.status_code == 200

    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration.name == new_configuration["name"]


@mark.asyncio
async def test_delete_configuration__success(
    backend_client: AsyncClient,
    inject_security_header,
    insert_objects,
    create_one_configuration,
    read_object,
    clean_up_database,
):
    id = create_one_configuration[0].id

    inject_security_header("owner1", Permissions.CONFIG_EDIT)
    response = await backend_client.delete(f"/lm/configurations/{id}")

    assert response.status_code == 200
    stmt = select(Configuration).where(Configuration.id == id)
    fetch_configuration = await read_object(stmt)

    assert fetch_configuration is None
