""" License-manager backend, command line entrypoint

Run with e.g. `uvicorn lm_backend.main:app` OR
set `licensemanager2.backend.main.handler` as the ASGI handler
"""
import logging
import sys
from contextlib import asynccontextmanager
from typing import cast

import sentry_sdk
from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from lm_backend import __version__
from lm_backend.api import api
from lm_backend.config import settings
from lm_backend.database import engine_factory

subapp = FastAPI(
    title="License Manager API",
    version=__version__,
    contact={
        "name": "Omnivector Solutions",
        "url": "https://www.omnivector.solutions/",
        "email": "info@omnivector.solutions",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/omnivector-solutions/license-manager/blob/main/LICENSE",
    },
    root_path=settings.ASGI_ROOT_PATH,
)

subapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

subapp.include_router(api)

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


@subapp.get(
    "/version",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "API version"}},
)
async def get_version():
    return __version__


app = FastAPI()
app.mount("/lm", subapp)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """
    Provide a lifespan context for the app.

    Will set up logging and cleanup database engines when the app is shut down.

    This is the preferred method of handling lifespan events in FastAPI.
    For more details, see: https://fastapi.tiangolo.com/advanced/events/
    """
    logger.remove()
    logger.add(sys.stderr, level=settings.LOG_LEVEL)
    logger.info(f"Logging configured 📝 Level: {settings.LOG_LEVEL}")

    if settings.LOG_LEVEL_SQL:
        level_sql = getattr(logging, settings.LOG_LEVEL_SQL)

        engine_logger = logging.getLogger("sqlalchemy.engine")
        engine_logger.setLevel(level_sql)

        logger.info(f"Database logging configured 📝 Level: {settings.LOG_LEVEL_SQL}")

    yield

    await engine_factory.cleanup()
