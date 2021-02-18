"""
Tests of the /license API endpoints
"""
from httpx import AsyncClient, Response
from pytest import fixture, mark
import respx


@fixture
def respx_mock():
    """
    Run a test in the respx context (similar to respx decorator, but it's a fixture)
    """
    with respx.mock as mock:
        yield mock


@fixture
def backend_responses(respx_mock: respx.MockRouter):
    """
    Backend placeholder with data similar to what we'd expect
    """
    respx_mock.route(method="GET", host="test", path="/api/v1/license/use/hello").mock(
        return_value=Response(
            status_code=200,
            json=[
                {
                    "product_feature": "hello.dolly",
                    "total": 80,
                    "booked": 11,
                    "available": 69,
                },
                {
                    "product_feature": "hello.world",
                    "total": 100,
                    "booked": 19,
                    "available": 81,
                },
            ],
        )
    )
    respx_mock.route(method="GET", host="test", path="/api/v1/license/all").mock(
        return_value=Response(
            status_code=200,
            json=[
                dict(product_feature="cool.beans", total=11, booked=11, available=0),
                dict(
                    product_feature="hello.dolly",
                    total=80,
                    booked=11,
                    available=69,
                ),
                dict(product_feature="hello.world", total=100, booked=19, available=81),
            ],
        )
    )


@mark.asyncio
async def test_licenses_product(agent_client: AsyncClient, backend_responses):
    """
    Do I fetch and order the licenses in the db?
    """
    resp = await agent_client.get("/api/v1/license/use/hello")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            product_feature="hello.dolly",
            total=80,
            booked=11,
            available=69,
        ),
        dict(product_feature="hello.world", total=100, booked=19, available=81),
    ]


@mark.asyncio
async def test_licenses_all(agent_client: AsyncClient, backend_responses):
    """
    Do I fetch and order the licenses in the db?
    """
    resp = await agent_client.get("/api/v1/license/all")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(product_feature="cool.beans", total=11, booked=11, available=0),
        dict(
            product_feature="hello.dolly",
            total=80,
            booked=11,
            available=69,
        ),
        dict(product_feature="hello.world", total=100, booked=19, available=81),
    ]
