"""
Boilerplate responses
"""
from fastapi import HTTPException, Request, Response
import httpx
from pydantic import BaseModel

from licensemanager2.backend.settings import SETTINGS


class OK(BaseModel):
    """
    A response that there was no error, when no other data is required
    """

    status: str = "ok"
    message: str = ""


def debug():
    """
    Enforce debug mode
    """
    if not SETTINGS.DEBUG:
        raise HTTPException(status_code=403)


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
