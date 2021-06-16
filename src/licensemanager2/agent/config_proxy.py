"""
Proxy a subset of the backend API to the backend
"""
from fastapi import APIRouter, Depends

from licensemanager2.agent.forward import ForwardOperation


config_proxy_router = APIRouter()


@config_proxy_router.get("/all")
async def all_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /all request to the backend and return the response
    """
    return await forward()


@config_proxy_router.get("/{id}")
async def job_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /job/{job_id} request to the backend and return the response
    """
    return await forward()


@config_proxy_router.post("/")
async def booking_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /book[PUT] request to the backend and return the response
    """
    return await forward()


@config_proxy_router.put("/{id}")
async def booking_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /book[PUT] request to the backend and return the response
    """
    return await forward()



@config_proxy_router.delete("/{id}")
async def booking_delete_forward(
    slug: str, forward: ForwardOperation = Depends(ForwardOperation)
):
    """
    Make a /book/{job_id}[DELETE] request to the backend and return the response
    """
    return await forward()