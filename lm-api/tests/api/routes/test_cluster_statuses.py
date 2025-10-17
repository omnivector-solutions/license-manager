import pendulum
from fastapi import status
from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_api.api.models.cluster_status import ClusterStatus
from lm_api.permissions import Permissions


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_cluster_status(
    permission, backend_client: AsyncClient, inject_security_header, read_object
):
    """Test adding a new cluster status."""
    cluster_client_id = "cluster_1"
    interval = 60

    inject_security_header("owner1@test.com", permission, client_id=cluster_client_id)

    pendulum.travel_to(pendulum.datetime(2024, 1, 1, 0, 0, 0), freeze=True)
    response = await backend_client.put("/lm/cluster_statuses", params={"interval": interval})
    assert response.status_code == status.HTTP_202_ACCEPTED

    stmt = select(ClusterStatus).where(ClusterStatus.cluster_client_id == cluster_client_id)
    cluster_status_fetched = await read_object(stmt)

    assert cluster_status_fetched.cluster_client_id == cluster_client_id
    assert cluster_status_fetched.interval == interval
    assert cluster_status_fetched.last_reported == pendulum.datetime(2024, 1, 1, 0, 0, 0)


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_cluster_status(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster_status,
    read_object,
):
    """Test updating an existing cluster status."""
    cluster_client_id = "dummy_1"
    interval = 120

    inject_security_header("owner1@test.com", permission, client_id=cluster_client_id)

    response = await backend_client.put("/lm/cluster_statuses", params={"interval": interval})
    assert response.status_code == status.HTTP_202_ACCEPTED


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_UPDATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_update_cluster_status__no_client_id(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
):
    """Test updating an existing cluster status without a client_id."""
    interval = 60

    inject_security_header("owner1@test.com", permission)

    response = await backend_client.put("/lm/cluster_statuses", params={"interval": interval})
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_read_all_cluster_statuses(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_cluster_statuses,
):
    """Test reading all cluster statuses."""
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/cluster_statuses")

    assert response.status_code == status.HTTP_200_OK

    cluster_statuses = response.json()
    assert len(cluster_statuses) == 2

    assert cluster_statuses[0]["cluster_client_id"] == "dummy_1"
    assert cluster_statuses[1]["cluster_client_id"] == "dummy_2"
    assert cluster_statuses[0]["interval"] == 60
    assert cluster_statuses[1]["interval"] == 60
    assert cluster_statuses[0]["last_reported"] == "2024-01-01T00:00:00+00:00"
    assert cluster_statuses[1]["last_reported"] == "2024-01-01T00:00:00+00:00"


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_read_cluster_status_by_client_id(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_cluster_status,
):
    """Test reading a specific cluster status."""
    inject_security_header("owner1@test.com", permission)

    response = await backend_client.get("/lm/cluster_statuses/dummy_1")
    assert response.status_code == status.HTTP_200_OK

    cluster_status = response.json()
    assert cluster_status["cluster_client_id"] == "dummy_1"
    assert cluster_status["interval"] == 60
    assert cluster_status["last_reported"] == "2024-01-01T00:00:00+00:00"


@mark.parametrize(
    "permission",
    [
        Permissions.STATUS_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_read_cluster_status_by_client_id__not_found(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
):
    """Test reading a specific cluster status that does not exist."""
    inject_security_header("owner1@test.com", permission)

    response = await backend_client.get("/lm/cluster_statuses/dummy_3")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Cluster with client_id dummy_3 not found."}
