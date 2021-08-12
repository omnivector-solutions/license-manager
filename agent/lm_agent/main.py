"""
License-manager agent, command line entrypoint

Run with e.g. `uvicorn lm_agent.main:app`
"""
import logging
import typing
from itertools import cycle

from fastapi import FastAPI, HTTPException
from fastapi_utils.tasks import repeat_every

from lm_agent.api import api_v1
from lm_agent.config import settings
from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile

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
