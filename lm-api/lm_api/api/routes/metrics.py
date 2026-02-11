from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from lm_api.database import SecureSession, secure_session
from lm_api.permissions import Permissions

router = APIRouter()


@router.get("/metrics")
def metrics(
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.METRICS_READ)),
):
    """
    Returns the current metrics.

    The data is cached in memory and updated periodically by the MetricsManager.
    Calling this endpoint does not trigger a metrics update, preventing potential performance issues.
    """
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
