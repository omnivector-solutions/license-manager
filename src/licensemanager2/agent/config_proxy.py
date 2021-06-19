"""
Proxy a subset of the backend API to the backend
"""
from fastapi import APIRouter, Depends

from licensemanager2.agent.forward import ForwardOperation


config_proxy_router = APIRouter()


@config_proxy_router.get("/all")
async def config_get_all_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a GET /config/all request to the backend and return the response
    """
    return await forward()


@config_proxy_router.get("/{id}")
async def config_get_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /config/{config_id}[GET] request to the backend and return the response
    """
    return await forward()


@config_proxy_router.post("/")
async def config_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /config/{config_id}[POST] request to the backend and return the response
    """
    return await forward()


@config_proxy_router.put("/{id}")
async def config_post_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /config/{config_id}[PUT] request to the backend and return the response
    """
    return await forward()


@config_proxy_router.delete("/{id}")
async def config_delete_forward(
    slug: str, forward: ForwardOperation = Depends(ForwardOperation)
):
    """
    Make a /config/{config_id}[DELETE] request to the backend and return the response
    """
    return await forward()