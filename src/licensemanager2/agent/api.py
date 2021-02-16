"""
Endpoints for the agent
"""
from fastapi import APIRouter

from licensemanager2.agent.license_proxy import license_proxy_router


api_v1 = APIRouter()

api_v1.include_router(license_proxy_router, prefix="/license", tags=["License"])
