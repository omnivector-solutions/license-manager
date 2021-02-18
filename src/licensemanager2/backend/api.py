"""
Endpoints for the backend
"""
from fastapi import APIRouter

from licensemanager2.backend.license import router_license


api_v1 = APIRouter()
api_v1.include_router(router_license, prefix="/license", tags=["License"])
