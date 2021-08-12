"""
Test that forward operation forwards requests
"""
from unittest.mock import AsyncMock, Mock, create_autospec

import httpx
import respx
from fastapi import Request, Response
from pytest import fixture, mark
from starlette.responses import Response

from lm_agent import forward


@mark.asyncio
async def test_make_request(agent_client):
    """
    Does the request adapt between request/response types?
    """

    async def mock_body():
        return b""

    mock_request = AsyncMock(
        spec=Request,
        url=Mock(path="/scary/ghost"),
        method="GET",
        body=mock_body,
    )
    with respx.mock:
        respx.get("/scary/ghost").mock(
            return_value=httpx.Response(
                200,
                json=["boo"],
            ),
        )
        forward_op = forward.ForwardOperation(mock_request)
        ret = await forward_op()
        assert ret.body == b'["boo"]'
        assert isinstance(ret, Response)


def test_async_client_cached():
    """
    Is the ForwardOperation.async_client cached between requests?
    """
    a1 = forward.async_client()
    a2 = forward.async_client()
    assert a1 is a2
