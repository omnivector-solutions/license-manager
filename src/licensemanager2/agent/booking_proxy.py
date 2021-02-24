"""
Proxy a subset of the backend API to the backend
"""
from fastapi import APIRouter, Depends

from licensemanager2.common_api import ForwardOperation


booking_proxy_router = APIRouter()


@booking_proxy_router.get("/all")
async def all_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /all request to the backend and return the response
    """
    return await forward()


@booking_proxy_router.get("/job/{slug}")
async def job_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /job/{job_id} request to the backend and return the response
    """
    return await forward()


@booking_proxy_router.put("/book")
async def booking_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /book[PUT] request to the backend and return the response
    """
    return await forward()


@booking_proxy_router.delete("/book/{slug}")
async def booking_delete_forward(
    slug: str, forward: ForwardOperation = Depends(ForwardOperation)
):
    """
    Make a /book/{job_id}[DELETE] request to the backend and return the response
    """
    return await forward()
