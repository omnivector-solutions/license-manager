from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.schemas.cluster import ClusterCreateSchema, ClusterSchema, ClusterUpdateSchema
#from lm_backend.api.schemas.cluster_configuration import ClusterCreateSchema, ClusterSchema, ClusterUpdateSchema
from lm_backend.crud import GenericCRUD
from lm_backend.database import get_session
from lm_backend.models.cluster import Cluster
#from lm_backend.models.cluster_configuration import Cluster

router = APIRouter()


crud = GenericCRUD(Cluster, ClusterCreateSchema, ClusterUpdateSchema)


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
    return await crud.create(db_session=db_session, obj=cluster)


@router.get("/", response_model=List[ClusterSchema], status_code=status.HTTP_200_OK)
async def read_all_clusters(db_session: AsyncSession = Depends(get_session)):
    """Return all clusters."""
    return await crud.read_all(db_session=db_session)


@router.get("/{cluster_id}", response_model=ClusterSchema, status_code=status.HTTP_200_OK)
async def read_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a cluster with the given id."""
    return await crud.read(db_session=db_session, id=cluster_id)


@router.put("/{cluster_id}", response_model=ClusterSchema, status_code=status.HTTP_200_OK)
async def update_cluster(
    cluster_id: int,
    cluster_update: ClusterUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a cluster in the database."""
    return await crud.update(
        db_session=db_session,
        id=cluster_id,
        obj=cluster_update,
    )


@router.delete("/{cluster_id}", status_code=status.HTTP_200_OK)
async def delete_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a cluster from the database."""
    await crud.delete(db_session=db_session, id=cluster_id)
    return {"message": "Cluster deleted successfully"}
