import asyncio

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from lm_api.api.metrics.collector import collect_feature_metrics
from lm_api.api.schemas.metrics import (
    LICENSE_TOTAL,
    LICENSE_USED,
)
from lm_api.config import settings
from lm_api.database import engine_factory


class MetricsManager:
    def __init__(self) -> None:
        self.task: asyncio.Task | None = None
        self._stop_event: asyncio.Event = asyncio.Event()

    async def update(self, session: AsyncSession | None = None) -> int:
        """
        Update the Prometheus metrics cache with current data.
        """
        close_session = session is None

        if session is None:
            session = engine_factory.get_session()

        try:
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

            feature_count = len(rows)
            logger.info(f"Updated metrics for {feature_count} features")
            return feature_count
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"Metrics update failed: {e}")
            raise
        finally:
            if close_session and session is not None:
                await session.close()

    async def run(self, interval: int) -> None:
        while not self._stop_event.is_set():
            await self.update()

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=interval,
                )
                break
            except asyncio.TimeoutError:
                continue

    async def start(self, interval: int | None) -> None:
        if self.is_running:
            return

        interval = interval or settings.METRICS_UPDATE_INTERVAL
        self._stop_event.clear()
        self.task = asyncio.create_task(self.run(interval))

    async def stop(self) -> None:
        task = self.task  # makes mypy happy
        if task is None or task.done():
            return

        self._stop_event.set()
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            self.task = None

    @property
    def is_running(self) -> bool:
        return self.task is not None and not self.task.done()


metrics_manager = MetricsManager()
