"""
License-manager backend, command line entrypoint

Run with e.g. `uvicorn licensemanager2.backend.main:app` OR
set `licensemanager2.backend.main.handler` as the ASGI handler
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from licensemanager2.backend import storage
from licensemanager2.backend.api import router_api_v1
from licensemanager2.backend.settings import SETTINGS
from licensemanager2.common_response import OK


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
    logging.getLogger().setLevel(level)


@app.on_event("startup")
async def init_database():
    """
    Connect the database; create it if necessary
    """
    storage.create_all_tables()
    await storage.database.connect()


@app.on_event("shutdown")
async def disconnect_database():
    """
    Disconnect the database
    """
    await storage.database.disconnect()


app.include_router(router_api_v1, prefix="/api/v1")

# ASGI adapter used for environments like API gateway
handler = Mangum(app)
