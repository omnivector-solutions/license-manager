"""
License-manager agent, command line entrypoint

Run with e.g. `uvicorn lm_agent.main:app`
"""
import logging
import typing
from itertools import cycle

import pkg_resources
from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every

from lm_agent.api import api_v1
from lm_agent.backend_utils import (
    LicenseManagerBackendConnectionError,
    LicenseManagerBackendVersionError,
)
from lm_agent.config import settings
from lm_agent.forward import async_client
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile

AGENT_VERSION = pkg_resources.get_distribution("license-manager-agent").version
BACKEND_VERSION = str()


app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=settings.ALLOW_ORIGINS_REGEX,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# app.add_middleware(TrustedHostMiddleware)
# app.add_middleware(ProxyHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def root():
    """
    Well, *something* should happen here.
    """
    return dict(message="OK")


@app.get("/debug")
async def debug():
    """
    Expose version information for the license-manager-{agent,backend}.
    """
    return dict(
        agent_version=AGENT_VERSION,
        backend_version=BACKEND_VERSION,
    )


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
    # Get the license-manager-backend version.
    global BACKEND_VERSION
    resp = await async_client().get("/version")
    # Check that we have a valid response.
    if resp.status_code != status.HTTP_200_OK:
        logger.error("license-manager-backend version could not be obtained.")
        raise LicenseManagerBackendConnectionError()

    # Check the version of the backend matches the version of the agent.
    BACKEND_VERSION = resp.json()["version"]
    if BACKEND_VERSION.split(".")[0] != AGENT_VERSION.split(".")[0]:
        logger.error(f"license-manager-backend incompatible version: {BACKEND_VERSION}.")
        raise LicenseManagerBackendVersionError()
    logger.info(f"license-manager-backend successfully connected. Version: {BACKEND_VERSION}.")


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
