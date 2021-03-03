"""
Tests of the /license API endpoints
"""
from httpx import AsyncClient
from pytest import fixture, mark


@fixture(autouse=True)
def responses(respx_mock):
    """
    Responses for all backend routes; protect real agent routes w/ pass_through
    """
    respx_mock.get("http://backend/api/v1/license/all") % dict(
        json=["congrats you called backend /license/all"]
    )
    respx_mock.get("http://backend/api/v1/license/use/hello") % dict(
        json=["congrats you called backend /license/use/hello"]
    )
    respx_mock.route(host="test").pass_through()
    return respx_mock


@mark.asyncio
async def test_licenses_product(agent_client: AsyncClient):
    """
    Do I fetch and order the licenses in the db?
    """
    resp = await agent_client.get("/api/v1/license/use/hello")
    assert resp.status_code == 200
    assert resp.json() == ["congrats you called backend /license/use/hello"]


@mark.asyncio
async def test_licenses_all(agent_client: AsyncClient):
    """
    Do I fetch and order the licenses in the db?
    """
    resp = await agent_client.get("/api/v1/license/all")
    assert resp.status_code == 200
    assert resp.json() == ["congrats you called backend /license/all"]
