import asyncio
import logging

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from lm_agent.backend_utils.utils import check_backend_health, report_cluster_status
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.scheduler import scheduler
from lm_agent.services.reconciliation import reconcile


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        sample_rate=settings.SENTRY_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILING_SAMPLE_RATE,
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        environment=settings.DEPLOY_ENV,
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.CRITICAL,
            ),
        ],
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
