#!/usr/bin/env python3
import asyncio
import logging
import typing

import pkg_resources
import sentry_sdk

from lm_agent.backend_utils import get_license_manager_backend_version
from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerBackendVersionError
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile

AGENT_VERSION = pkg_resources.get_distribution("license-manager-agent").version

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        sample_rate=typing.cast(float, settings.SENTRY_SAMPLE_RATE),  # The cast silences mypy
        environment=settings.DEPLOY_ENV,
    )


async def backend_version_check():
    """Check that the license-manager-backend version matches our own."""

    # Get the backend_version and check that the major version matches our own.
    backend_version = await get_license_manager_backend_version()
    logger.info(f"Agent Version: {AGENT_VERSION}")
    logger.info(f"Backend Version: {backend_version}")
    if backend_version.split(".")[0] != AGENT_VERSION.split(".")[0]:
        logger.error(f"license-manager-backend incompatible version: {backend_version}.")
        raise LicenseManagerBackendVersionError()
    logger.info("license-manager-backend successfully connected.")


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
    await backend_version_check()
    await reconcile()
    logger.info("Reconcile completed successfully")


def main():
    asyncio.run(run_reconcile())
