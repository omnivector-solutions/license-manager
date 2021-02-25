"""
Test that forward operation forwards requests
"""
from unittest.mock import Mock, create_autospec

from fastapi import Request, Response
from pytest import fixture, mark
import respx

from licensemanager2.agent import forward


@fixture
def forward_op(fastapi_request):
    return forward.ForwardOperation(fastapi_request)


@fixture
def fastapi_request():
    ret = create_autospec(
        Request,
        url=Mock(path="/scary/ghost"),
        method="GET",
    )
    return ret


@fixture
def spooky_responses(respx_mock: respx.MockRouter):
    """
    Respond to some ghastly requests
    """
    respx_mock.get("/scary/ghost") % dict(json=["boo"])


@mark.asyncio
async def test_make_request(forward_op, agent_client, spooky_responses):
    """
    Does the request adapt between request/response types?
    """
    ret = await forward_op()
    assert ret.body == b'["boo"]'
    assert isinstance(ret, Response)


def test_async_client_cached(forward_op):
    """
    Is the ForwardOperation.async_client cached between requests?
    """
    a1 = forward_op.async_client
    a2 = forward_op.async_client
    assert a1 is a2
