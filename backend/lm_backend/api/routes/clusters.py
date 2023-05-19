from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.cluster import Cluster
from lm_backend.api.schemas.cluster import ClusterCreateSchema, ClusterSchema, ClusterUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_cluster = GenericCRUD(Cluster, ClusterCreateSchema, ClusterUpdateSchema)


@router.post(
    "/",
    response_model=ClusterSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_EDIT))],
)
async def create_cluster(
    cluster: ClusterCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new cluster."""
    return await crud_cluster.create(db_session=db_session, obj=cluster)


@router.get(
    "/",
    response_model=List[ClusterSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_VIEW))],
)
async def read_all_clusters(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all clusters with the associated configurations."""
    return await crud_cluster.read_all(
        db_session=db_session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/by_client_id/{client_id}",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_VIEW))],
)
async def read_cluster_by_client_id(
    client_id: str = Query(None),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all clusters with the associated configurations."""
    return await crud_cluster.filter(
        db_session=db_session, filter_field=Cluster.client_id, filter_term=client_id
    )


@router.get(
    "/{cluster_id}",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_VIEW))],
)
async def read_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a cluster with the associated configurations with the given id."""
    return await crud_cluster.read(db_session=db_session, id=cluster_id)


@router.put(
    "/{cluster_id}",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_EDIT))],
)
async def update_cluster(
    cluster_id: int,
    cluster_update: ClusterUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a cluster in the database."""
    return await crud_cluster.update(
        db_session=db_session,
        id=cluster_id,
        obj=cluster_update,
    )


@router.delete(
    "/{cluster_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CLUSTER_EDIT))],
)
async def delete_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Delete a cluster from the database.

    This will also delete all configurations associated with the cluster.
    """
    return await crud_cluster.delete(db_session=db_session, id=cluster_id)
