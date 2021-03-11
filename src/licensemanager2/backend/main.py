"""
License-manager backend, command line entrypoint

Run with e.g. `uvicorn licensemanager2.backend.main:app` OR
set `licensemanager2.backend.main.handler` as the ASGI handler
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from licensemanager2.backend import logger, storage
from licensemanager2.backend.api import api_v1
from licensemanager2.backend.settings import SETTINGS
from licensemanager2.common_api import OK


app = FastAPI(root_path=SETTINGS.ASGI_ROOT_PATH)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=SETTINGS.ALLOW_ORIGINS_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# app.add_middleware(TrustedHostMiddleware)
# app.add_middleware(ProxyHeadersMiddleware)
# app.add_middleware(RateLimitMiddleware)


@app.get("/")
async def root():
    """
    Well, *something* should happen here.
    """
    return OK()


@app.get("/health")
async def health():
    """
    Healthcheck, for health monitors in the deployed environment
    """
    return OK()


@app.on_event("startup")
def begin_logging():
    """
    Configure logging
    """
    if SETTINGS.LOG_LEVEL_SQL:
        level_sql = getattr(logging, SETTINGS.LOG_LEVEL_SQL)
        engine_logger = logging.getLogger("sqlalchemy.engine")
        engine_logger.setLevel(level_sql)
        databases_logger = logging.getLogger("databases")
        databases_logger.setLevel(level_sql)

    level = getattr(logging, SETTINGS.LOG_LEVEL)
    logger.setLevel(level)

    logger.info(
        f"Logging configured 📝 Handlers: {logger.handlers} Level: {logger.level}"
    )


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


app.include_router(api_v1, prefix="/api/v1")


def handler(event, context):
    """
    Adapt inbound ASGI requests (from API Gateway) using Mangum

    - Assumes non-ASGI requests (from any other source) are a cloudwatch ping
    """
    if not event.get("requestContext"):
        logger.info("☁️ ☁️ ☁️ cloudwatch keep-warm ping ☁️ ☁️ ☁️")
        return

    mangum = Mangum(app)
    return mangum(event, context)
