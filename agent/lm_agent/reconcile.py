#!/usr/bin/env python3
import asyncio
import logging
import typing

import sentry_sdk

from lm_agent.backend_utils import check_backend_health
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        sample_rate=typing.cast(float, settings.SENTRY_SAMPLE_RATE),  # The cast silences mypy
        environment=settings.DEPLOY_ENV,
    )


def begin_logging():
    """Configure logging."""
    init_logging("license-manager-agent")

    level = getattr(logging, settings.LOG_LEVEL)
    logger.setLevel(level)
    logger.info(f"Backend URL: {settings.BACKEND_BASE_URL}")


async def run_reconcile():
    """Main function to setup the env and call the reconcile function."""
    begin_logging()
    logger.info("Starting reconcile script")
    await check_backend_health()
    await reconcile()
    logger.info("Reconcile completed successfully")


def main():
    asyncio.run(run_reconcile())
