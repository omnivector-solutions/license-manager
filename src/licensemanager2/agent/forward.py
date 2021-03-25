"""
Forwarding a requested URL to a remote server and returning the response
"""
from functools import lru_cache

from fastapi import Request, Response
import httpx

from licensemanager2.agent import logger
from licensemanager2.agent.settings import SETTINGS


@lru_cache
def async_client() -> httpx.AsyncClient:
    """
    HTTPX client that authenticates with & makes requests to the l-m backend

    Memoized for reuse and connection pooling
    """

    def _auth(request):
        request.headers["authorization"] = f"Bearer {SETTINGS.BACKEND_API_TOKEN}"
        return request

    return httpx.AsyncClient(base_url=SETTINGS.BACKEND_BASE_URL, auth=_auth)


class ForwardOperation:
    """
    Forward an inbound request to the agent to the backend, and return
    the backend's response.

    Inject as a FastAPI path parameter with Depends.
    """

    def __init__(self, req: Request):
        self.request = req

    async def __call__(self):
        """
        Make the backend request and bring back the response
        """
        httpx_req = await self._adapt_request_fastapi_to_httpx(self.request)
        httpx_resp = await async_client().send(httpx_req)
        resp = self._adapt_response_httpx_to_fastapi(httpx_resp)
        return resp

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

    async def _adapt_request_fastapi_to_httpx(self, req: Request) -> httpx.Request:
        """
        FastAPI Request becomes HTTPX Request to talk to the backend
        """
        url = f"{SETTINGS.BACKEND_BASE_URL}{req.url.path}"
        logger.debug(f"Forwarding request to {url}")
        _headers = req.headers.mutablecopy()

        # if there's authorization attached, get rid of it, we will replace it with our own
        if _headers["authorization"]:
            logger.warning(
                "Authorization header is being dropped, to substitute the value of BACKEND_API_TOKEN."
            )
            del _headers["authorization"]

        # the incoming host header will be the agent's netloc, we don't want to send that to a different server.
        del _headers["host"]

        # both of the removed headers will be set by httpx

        ret = async_client().build_request(
            req.method, url, headers=_headers.items(), content=await req.body()
        )
        return ret
