"""
Proxy a subset of the backend API to the backend
"""
from fastapi import APIRouter, Depends

from licensemanager2.common_api import ForwardOperation


license_proxy_router = APIRouter()


@license_proxy_router.get("/all")
async def all_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /all request to the backend and return the response
    """
    return await forward()


@license_proxy_router.get("/use/{slug}")
async def use_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /use request to the backend and return the response
    """
    return await forward()
