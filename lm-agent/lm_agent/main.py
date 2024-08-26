import asyncio
import typing

import sentry_sdk

from lm_agent.backend_utils.utils import check_backend_health, report_cluster_status
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.scheduler import scheduler
from lm_agent.services.reconciliation import reconcile


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        sample_rate=typing.cast(float, settings.SENTRY_SAMPLE_RATE),  # The cast silences mypy
        environment=settings.DEPLOY_ENV,
    )


async def scheduled_tasks():
    """
    The scheduled tasks to be run by the agent.
    """
    await check_backend_health()
    await report_cluster_status()
    await reconcile()


def main():
    """
    Main function to run the scheduled tasks.
    """
    init_logging("license-manager-agent")
    logger.info("Starting License Manager Agent")

    scheduler.start()
    scheduler.add_job(scheduled_tasks)

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        logger.info("Stopping License Manager Agent")
        scheduler.stop()


if __name__ == "__main__":
    main()
