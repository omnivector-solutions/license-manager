"""
Endpoints for the agent
"""
from fastapi import APIRouter

from licensemanager2.agent.booking_proxy import booking_proxy_router
from licensemanager2.agent.license_proxy import license_proxy_router
from licensemanager2.agent.config_proxy import config_proxy_router


api_v1 = APIRouter()

api_v1.include_router(license_proxy_router, prefix="/license", tags=["License"])
api_v1.include_router(booking_proxy_router, prefix="/booking", tags=["License"])
api_v1.include_router(config_proxy_router, prefix="/config", tags=["Config"])
