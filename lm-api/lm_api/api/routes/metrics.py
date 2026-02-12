from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from lm_api.database import SecureSession, secure_session
from lm_api.metrics import metrics_collector
from lm_api.permissions import Permissions

router = APIRouter()


@router.get("")
def metrics(
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.METRICS_READ)),
):
    """
    Read-only endpoint to expose metrics for Prometheus.

    The metrics are collected using the MetricsCollector class, which queries
    the database for license usage information and formats it for Prometheus.
    """
    return Response(
        generate_latest(metrics_collector.registry),
        media_type=CONTENT_TYPE_LATEST,
    )
