from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.cluster import Cluster
from lm_backend.api.schemas.cluster import ClusterCreateSchema, ClusterSchema, ClusterUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.database import secure_session, SecureSession

router = APIRouter()


crud_cluster = GenericCRUD(Cluster, ClusterCreateSchema, ClusterUpdateSchema)


@router.post(
    "/",
    response_model=ClusterSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_cluster(
    cluster: ClusterCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_EDIT)),
):
    """Create a new cluster."""
    return await crud_cluster.create(db_session=secure_session.session, obj=cluster)


@router.get(
    "/",
    response_model=List[ClusterSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_clusters(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_VIEW)),
):
    """Return all clusters with the associated configurations."""
    return await crud_cluster.read_all(
        db_session=secure_session.session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/by_client_id",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
)
async def read_cluster_by_client_id(
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_VIEW)),
):
    """Return a the cluster with the specified client_id with the associated configurations."""
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    return await crud_cluster.filter(
        db_session=secure_session.session, filter_field=Cluster.client_id, filter_term=client_id
    )


@router.get(
    "/{cluster_id}",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
)
async def read_cluster(
    cluster_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_VIEW)),
):
    """Return a cluster with the associated configurations with the given id."""
    return await crud_cluster.read(db_session=secure_session.session, id=cluster_id)


@router.put(
    "/{cluster_id}",
    response_model=ClusterSchema,
    status_code=status.HTTP_200_OK,
)
async def update_cluster(
    cluster_id: int,
    cluster_update: ClusterUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_EDIT)),
):
    """Update a cluster in the database."""
    return await crud_cluster.update(
        db_session=secure_session.session,
        id=cluster_id,
        obj=cluster_update,
    )


@router.delete(
    "/{cluster_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_cluster(
    cluster_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.CLUSTER_EDIT)),
):
    """
    Delete a cluster from the database.

    This will also delete all configurations associated with the cluster.
    """
    return await crud_cluster.delete(db_session=secure_session.session, id=cluster_id)
