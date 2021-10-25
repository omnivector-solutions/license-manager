"""
Forwarding a requested URL to a remote server and returning the response
"""
from functools import lru_cache

import httpx

from lm_agent.config import settings


@lru_cache
def async_client() -> httpx.AsyncClient:
    """
    HTTPX client that authenticates with & makes requests to the l-m backend

    Memoized for reuse and connection pooling
    """

    def _auth(request):
        request.headers["authorization"] = f"Bearer {settings.BACKEND_API_TOKEN}"
        return request

    return httpx.AsyncClient(base_url=settings.BACKEND_BASE_URL, auth=_auth)
