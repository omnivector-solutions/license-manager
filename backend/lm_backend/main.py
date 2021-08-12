""" License-manager backend, command line entrypoint

Run with e.g. `uvicorn lm_backend.main:app` OR
set `licensemanager2.backend.main.handler` as the ASGI handler
"""
import logging
import sys
from typing import Any, Optional

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from mangum import Mangum
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from lm_backend import storage
from lm_backend.api import api_v1
from lm_backend.config import settings

app: Any = FastAPI(root_path=settings.ASGI_ROOT_PATH)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=settings.ALLOW_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1, prefix="/api/v1")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0,
    )

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


@app.on_event("startup")
def begin_logging():
    """
    Configure logging
    """
    logger.remove()
    logger.add(sys.stderr, level=settings.LOG_LEVEL)
    logger.info(f"Logging configured 📝 Level: {settings.LOG_LEVEL}")

    if settings.LOG_LEVEL_SQL:
        level_sql = getattr(logging, settings.LOG_LEVEL_SQL)

        engine_logger = logging.getLogger("sqlalchemy.engine")
        engine_logger.setLevel(level_sql)

        databases_logger = logging.getLogger("databases")
        databases_logger.setLevel(level_sql)

        logger.info(f"Database logging configured 📝 Level: {settings.LOG_LEVEL_SQL}")


@app.on_event("startup")
async def init_database():
    """
    Connect the database; create it if necessary
    """
    storage.create_all_tables()
    await storage.database.connect()
    logger.info("Database configured 💽")


@app.on_event("shutdown")
async def disconnect_database():
    """
    Disconnect the database
    """
    await storage.database.disconnect()


if settings.SENTRY_DSN:
    app = SentryAsgiMiddleware(app)


def handler(event: dict, context: dict) -> Optional[dict]:
    """
    Adapt inbound ASGI requests (from API Gateway) using Mangum

    - Assumes non-ASGI requests (from any other source) are a cloudwatch ping
    """
    if not event.get("requestContext"):
        logger.info("☁️ ☁️ ☁️ cloudwatch keep-warm ping ☁️ ☁️ ☁️")
        return None

    mangum = Mangum(app)
    return mangum(event, context)
