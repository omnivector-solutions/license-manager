"""
License-manager agent, command line entrypoint

Run with e.g. `uvicorn licensemanager2.agent.main:app`
"""
import logging

from fastapi import FastAPI

from licensemanager2.agent.api import api_v1
from licensemanager2.agent.settings import SETTINGS
from licensemanager2.common_response import OK


app = FastAPI()
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=SETTINGS.ALLOW_ORIGINS_REGEX,
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
    level = getattr(logging, SETTINGS.LOG_LEVEL)
    logging.getLogger().setLevel(level)


app.include_router(api_v1, prefix="/api/v1")
