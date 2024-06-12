"""Cluster status API endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pendulum.datetime import DateTime as PendulumDateTime

from lm_api.api.cruds.cluster_status import ClusterStatusCRUD
from lm_api.api.models.cluster_status import ClusterStatus
from lm_api.api.schemas.cluster_status import ClusterStatusSchema
from lm_api.database import SecureSession, secure_session
from lm_api.permissions import Permissions
from buzz import require_condition


router = APIRouter()
crud_cluster_status = ClusterStatusCRUD(ClusterStatus)


@router.put(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    description="Endpoints to accept a status check from the agent on the clusters.",
)
async def report_cluster_status(
    interval: int = Query(description="The interval in seconds between pings.", gt=0),
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.STATUS_UPDATE)),
):
    """
    Report the status of the cluster.
    """
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    cluster_status = ClusterStatusSchema(
        cluster_client_id=secure_session.identity_payload.client_id,
        interval=interval,
        last_reported=PendulumDateTime.utcnow(),
    )

    return await crud_cluster_status.upsert(db_session=secure_session.session, payload=cluster_status)


@router.get(
    "",
    description="Endpoint to get the status of all clusters.",
    response_model=List[ClusterStatusSchema],
)
async def read_all_cluster_statuses(
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.STATUS_READ, commit=False)
    ),
):
    """
    Get the status of the cluster.
    """
    return await crud_cluster_status.read_all(
        db_session=secure_session.session,
    )


@router.get(
    "/{cluster_client_id}",
    description="Endpoint to get the status of a specific cluster.",
    response_model=Optional[ClusterStatusSchema],
)
async def read_cluster_status_by_client_id(
    cluster_client_id: str,
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.STATUS_READ, commit=False)
    ),
):
    """
    Get the status of a specific cluster.

    There should only be one status per cluster.
    """
    cluster_statuses = await crud_cluster_status.filter(
        db_session=secure_session.session,
        filter_expressions=[ClusterStatus.cluster_client_id == cluster_client_id],
    )

    require_condition(
        len(cluster_statuses) <= 1,
        "There should only be one status per cluster.",
        raise_exc_class=HTTPException,
        raise_kwargs=dict(
            status_code=status.HTTP_400_BAD_REQUEST, detail="There should only be one status per cluster."
        ),
    )

    if not cluster_statuses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cluster with client_id {cluster_client_id} not found.",
        )

    return cluster_statuses[0]
