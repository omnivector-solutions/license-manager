from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.cluster import Cluster
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_cluster__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    clean_up_database,
):
    data = {
        "name": "Dummy Cluster",
        "client_id": "dummy",
    }

    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.post("/lm/clusters", json=data)
    assert response.status_code == 201

    stmt = select(Cluster).where(Cluster.name == data["name"])
    fetched = await read_object(stmt)

    assert fetched.name == data["name"]
    assert fetched.client_id == data["client_id"]


@mark.asyncio
async def test_get_all_clusters__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_clusters,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    response = await backend_client.get("/lm/clusters")

    assert response.status_code == 200

    response_clusters = response.json()
    assert response_clusters[0]["name"] == create_clusters[0].name
    assert response_clusters[0]["client_id"] == create_clusters[0].client_id
    assert response_clusters[1]["name"] == create_clusters[1].name
    assert response_clusters[1]["client_id"] == create_clusters[1].client_id


@mark.asyncio
async def test_get_all_clusters__with_search(
    backend_client: AsyncClient,
    inject_security_header,
    create_clusters,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    client_id = create_clusters[1].client_id
    response = await backend_client.get(f"/lm/clusters/?search={client_id}")

    assert response.status_code == 200

    response_cluster = response.json()
    assert response_cluster[0]["name"] == create_clusters[1].name
    assert response_cluster[0]["client_id"] == create_clusters[1].client_id


@mark.asyncio
async def test_get_all_clusters__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_clusters,
    clean_up_database,
):
    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    response = await backend_client.get("/lm/clusters/?sort_field=name&sort_ascending=false")

    assert response.status_code == 200

    response_clusters = response.json()
    assert response_clusters[0]["name"] == create_clusters[1].name
    assert response_clusters[0]["client_id"] == create_clusters[1].client_id
    assert response_clusters[1]["name"] == create_clusters[0].name
    assert response_clusters[1]["client_id"] == create_clusters[0].client_id


@mark.asyncio
async def test_get_cluster__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
):
    id = create_one_cluster[0].id

    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    response = await backend_client.get(f"/lm/clusters/{id}")

    assert response.status_code == 200

    response_cluster = response.json()
    assert response_cluster["name"] == create_one_cluster[0].name
    assert response_cluster["client_id"] == create_one_cluster[0].client_id


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_cluster__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
    id,
):
    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    response = await backend_client.get(f"/lm/clusters/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_get_cluster_by_client_id__success(
    backend_client: AsyncClient,
    inject_security_header,
    inject_client_id_in_security_header,
    create_one_cluster,
    clean_up_database,
):
    client_id = create_one_cluster[0].client_id

    inject_client_id_in_security_header(client_id, Permissions.CLUSTER_VIEW)

    response = await backend_client.get("/lm/clusters/by_client_id")

    assert response.status_code == 200

    response_cluster = response.json()
    assert response_cluster["name"] == create_one_cluster[0].name
    assert response_cluster["client_id"] == create_one_cluster[0].client_id


@mark.parametrize(
    "client_id",
    [
        "invalid_id_123",
        "non_existent_id",
        999999999,
    ],
)
@mark.asyncio
async def test_get_cluster_by_client_id__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
    client_id,
):
    inject_security_header("owner1", Permissions.CLUSTER_VIEW)
    response = await backend_client.get(f"/lm/clusters/by_client_id/{client_id}")

    assert response.status_code == 404


@mark.asyncio
async def test_update_cluster__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    read_object,
    clean_up_database,
):
    new_cluster = {"name": "New Dummy Cluster", "client_id": "new-dummy"}

    id = create_one_cluster[0].id

    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.put(f"/lm/clusters/{id}", json=new_cluster)

    assert response.status_code == 200

    stmt = select(Cluster).where(Cluster.id == id)
    fetch_cluster = await read_object(stmt)

    assert fetch_cluster.name == new_cluster["name"]
    assert fetch_cluster.client_id == new_cluster["client_id"]


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_update_cluster__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
    id,
):
    new_cluster = {"name": "New Dummy Cluster", "client_id": "new-dummy"}

    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.put(f"/lm/clusters/{id}", json=new_cluster)

    assert response.status_code == 404


@mark.asyncio
async def test_update_cluster__fail_with_bad_data(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
):
    new_cluster = {"bla": "bla"}

    id = create_one_cluster[0].id

    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.put(f"/lm/clusters/{id}", json=new_cluster)

    assert response.status_code == 400


@mark.asyncio
async def test_delete_cluster__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    read_object,
    clean_up_database,
):
    id = create_one_cluster[0].id

    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.delete(f"/lm/clusters/{id}")

    assert response.status_code == 200
    stmt = select(Cluster).where(Cluster.id == id)
    fetch_cluster = await read_object(stmt)

    assert fetch_cluster is None


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_delete_cluster__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster,
    clean_up_database,
    id,
):
    inject_security_header("owner1", Permissions.CLUSTER_EDIT)
    response = await backend_client.delete(f"/lm/clusters/{id}")

    assert response.status_code == 404
