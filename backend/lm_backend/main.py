""" License-manager backend, command line entrypoint

Run with e.g. `uvicorn lm_backend.main:app` OR
set `licensemanager2.backend.main.handler` as the ASGI handler
"""
import logging
import sys
from typing import cast

import sentry_sdk
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from lm_backend import storage
from lm_backend.api import api_v1
from lm_backend.config import settings

subapp = FastAPI(root_path=settings.ASGI_ROOT_PATH)
subapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

subapp.include_router(api_v1, prefix="/api/v1")

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        sample_rate=cast(float, settings.SENTRY_SAMPLE_RATE),  # The cast silences mypy
        environment=settings.DEPLOY_ENV,
    )
    subapp.add_middleware(SentryAsgiMiddleware)


@subapp.get(
    "/health",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "API is healthy"}},
)
async def health_check():
    return Response(status_code=status.HTTP_204_NO_CONTENT)


app = FastAPI()
app.mount("/lm", subapp)


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
