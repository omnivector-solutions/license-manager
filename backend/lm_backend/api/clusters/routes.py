from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from lm_backend.api.schemas import ClusterCreateSchema, ClusterSchema, ClusterUpdateSchema
from lm_backend.api.crud import GenericCRUD
from lm_backend.api.clusters.crud import ClusterCRUD
from lm_backend.database import get_session
from lm_backend.models import Cluster
from sqlalchemy.orm import selectinload

router = APIRouter()


#crud_cluster = ClusterCRUD(Cluster, ClusterCreateSchema, ClusterUpdateSchema)
crud_cluster = GenericCRUD(Cluster, ClusterCreateSchema, ClusterUpdateSchema)


@router.post(
    "/",
    response_model=ClusterSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_cluster(
    cluster: ClusterCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new cluster."""
    return await crud_cluster.create(db_session=db_session, obj=cluster)


@router.get("/", response_model=List[ClusterSchema], status_code=status.HTTP_200_OK)
async def read_all_clusters(db_session: AsyncSession = Depends(get_session)):
    """Return all clusters."""
    return await crud_cluster.read_all(db_session=db_session, options=selectinload(Cluster.configurations))


@router.get("/{cluster_id}", response_model=ClusterSchema, status_code=status.HTTP_200_OK)
async def read_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a cluster with the given id."""
    return await crud_cluster.read(db_session=db_session, id=cluster_id)


@router.put("/{cluster_id}", response_model=ClusterSchema, status_code=status.HTTP_200_OK)
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


@router.delete("/{cluster_id}", status_code=status.HTTP_200_OK)
async def delete_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a cluster from the database."""
    await crud_cluster.delete(db_session=db_session, id=cluster_id)
    return {"message": "Cluster deleted successfully"}
