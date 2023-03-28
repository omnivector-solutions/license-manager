from typing import List, Optional

from fastapi import APIRouter, Depends, Body, HTTPException, status


from lm_backend.api.cluster.crud import ClusterCRUD
from lm_backend.api.cluster.dependencies import get_cluster_crud
from lm_backend.api.cluster.schemas import ClusterCreateRequest, ClusterResponse

router = APIRouter()


@router.post("/", response_model=ClusterResponse)
async def create_cluster(
    cluster: ClusterCreateRequest,
    cluster_crud: ClusterCRUD = Depends(get_cluster_crud),
):
    """Create a new cluster."""
    try:
        return cluster_crud.create(cluster=cluster)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[ClusterResponse])
async def read_all_clusters(cluster_crud: ClusterCRUD = Depends(get_cluster_crud)):
    """Return all clusters."""
    return await cluster_crud.read_all()


@router.get("/{cluster_id}", response_model=ClusterResponse)
async def read_cluster(
    cluster_id: int, cluster_crud: ClusterCRUD = Depends(get_cluster_crud)
):
    """Return a cluster with the given id."""
    cluster = await cluster_crud.read(cluster_id=cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    return cluster


@router.put("/{cluster_id}", response_model=ClusterResponse)
async def update_cluster(
    cluster_id: int,
    name: Optional[str] = Body(None),
    client_id: Optional[str] = Body(None),
    cluster_crud: ClusterCRUD = Depends(get_cluster_crud),
):
    """Update a cluster in the database."""
    cluster = await cluster_crud.read(cluster_id)
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")

    try:
        return await cluster_crud.update(
            cluster_id=cluster_id, name=name, client_id=client_id
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: int, cluster_crud: ClusterCRUD = Depends(get_cluster_crud)
):
    """Delete a cluster from the database."""
    cluster = await cluster_crud.read(cluster_id)
    if not cluster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    try:
        deleted = cluster_crud.delete(cluster_id=cluster_id)
        if deleted:
            return status.HTTP_204_NO_CONTENT
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
