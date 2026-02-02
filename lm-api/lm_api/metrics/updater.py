import asyncio
import logging

from lm_api.database import engine_factory
from lm_api.metrics.collector import collect_feature_metrics
from lm_api.metrics.schema import (
    LICENSE_TOTAL,
    LICENSE_USED,
)

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = 60  # seconds


async def metrics_loop():
    while True:
        session = None
        try:
            session = engine_factory.get_session()

            rows = await collect_feature_metrics(session)

            LICENSE_TOTAL.clear()
            LICENSE_USED.clear()

            for r in rows:
                labels = {
                    "cluster": r.cluster,
                    "product": r.product,
                    "feature": r.feature,
                }

                LICENSE_TOTAL.labels(**labels).set(r.total)
                LICENSE_USED.labels(**labels).set(r.used)

        except Exception:
            logger.exception("Metrics update failed")

        finally:
            if session is not None:
                await session.close()

        await asyncio.sleep(REFRESH_INTERVAL)
