"""
Endpoints for the agent
"""
from fastapi import APIRouter

from licensemanager2.agent.license_proxy import license_proxy_router


api_v1 = APIRouter()

blah_router = APIRouter()
@blah_router.get("/hello")
def hello():
    return "hello"


api_v1.include_router(license_proxy_router, prefix="/license", tags=["License"])
api_v1.include_router(blah_router, prefix="/blah")
