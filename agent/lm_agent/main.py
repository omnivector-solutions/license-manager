"""
License-manager agent, command line entrypoint

Run with e.g. `uvicorn lm_agent.main:app`
"""
import logging

import pkg_resources
import sentry_sdk
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from lm_agent.api import api_v1
from lm_agent.backend_utils import LicenseManagerBackendVersionError, get_license_manager_backend_version
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile

AGENT_VERSION = pkg_resources.get_distribution("license-manager-agent").version


app = FastAPI()
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )
    app.add_middleware(SentryAsgiMiddleware)


@app.get("/")
async def root():
    """
    Well, *something* should happen here.
    """
    return dict(message="OK")


@app.get("/health")
async def health():
    """
    Healthcheck, for health monitors in the deployed environment
    """
    return dict(message="OK")


@app.get("/reconcile")
async def reconcile_endpoint():
    """
    Force a reconciliation by making a get request to this endpoint.
    """
    await reconcile()


@app.on_event("startup")
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


@app.on_event("startup")
def begin_logging():
    """
    Configure logging
    """
    init_logging("license-manager-agent")

    level = getattr(logging, settings.LOG_LEVEL)
    logger.setLevel(level)

    # as a developer you'll run this with uvicorn,
    # which takes over logging.
    uvicorn = logging.getLogger("uvicorn")
    if uvicorn.handlers:  # pragma: nocover
        logger.addHandler(uvicorn.handlers[0])

    logger.info(f"Forwarding requests ⇒ {settings.BACKEND_BASE_URL}")


@app.on_event("startup")
@repeat_every(
    seconds=settings.STAT_INTERVAL,
    logger=logger,
    raise_exceptions=True,
)
async def collect_stats():
    """
    Periodically get license stats and report them to the backend
    """
    logger.info("⏲️ 📒 begin stat collection")
    return await reconcile()


app.include_router(api_v1, prefix="/api/v1")
