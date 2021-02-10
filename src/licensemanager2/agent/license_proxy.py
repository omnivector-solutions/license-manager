"""
Proxy a subset of the backend API to the backend
"""
from fastapi import APIRouter, Depends, Request, Response
import httpx

from licensemanager2.agent.settings import SETTINGS


license_proxy_router = APIRouter()


class ForwardOperation:
    """
    Forward an inbound request to the agent to the backend, and return
    the backend's response.

    Inject as a FastAPI path parameter with Depends.
    """

    _async_client = None

    def __init__(self, req: Request):
        self.request = req

    async def __call__(self):
        """
        Make the backend request and bring back the response
        """
        httpx_req = await self._adapt_request_fastapi_to_httpx(self.request)
        httpx_resp = await self.async_client.send(httpx_req)
        resp = self._adapt_response_httpx_to_fastapi(httpx_resp)
        return resp

    @property
    def async_client(self) -> httpx.AsyncClient:
        """
        An httpx client

        Memoized for reuse and connection pooling
        """
        if ForwardOperation._async_client is None:
            ForwardOperation._async_client = httpx.AsyncClient(
                base_url=SETTINGS.BACKEND_BASE_URL,
            )

        return ForwardOperation._async_client

    @staticmethod
    def _adapt_response_httpx_to_fastapi(resp: httpx.Response) -> Response:
        """
        HTTPX Response becomes FastAPI Response to return the backend response
        """
        ret = Response()
        ret.body = resp.content
        ret.init_headers(resp.headers)
        ret.status_code = resp.status_code
        return ret

    @staticmethod
    async def _adapt_request_fastapi_to_httpx(req: Request) -> httpx.Request:
        """
        FastAPI Request becomes HTTPX Request to talk to the backend
        """
        url = f"{SETTINGS.BACKEND_BASE_URL}{req.url.path}"
        ret = httpx.Request(
            req.method, url, headers=req.headers.items(), content=await req.body()
        )
        return ret


@license_proxy_router.get("/use/{slug}")
async def use_forward(slug: str, forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /use request to the backend and return the response
    """
    return await forward()


@license_proxy_router.put("/booking")
async def booking_put_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /booking[PUT] request to the backend and return the response
    """
    return await forward()


@license_proxy_router.delete("/booking")
async def booking_delete_forward(forward: ForwardOperation = Depends(ForwardOperation)):
    """
    Make a /booking[DELETE] request to the backend and return the response
    """
    return await forward()
