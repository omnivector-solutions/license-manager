"""
Proxy a subset of the backend API to the backend
"""
from typing import Callable

from fastapi import APIRouter, Request, Response
from fastapi.routing import APIRoute
import httpx


class ProxyingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def proxy_license_api(request: Request) -> Response:
            print(request)
            client = httpx.AsyncClient()
            response = await client.get("https://example.com/")
            return response

            # TODO: /reconcile should be forbidden

        return proxy_license_api


license_proxy_router = APIRouter(route_class=ProxyingRoute)
