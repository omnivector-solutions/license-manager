"""
Test whether routes are forwarded
"""
import re

from httpx import AsyncClient
from pytest import fixture, mark


@fixture(autouse=True)
def responses(respx_mock):
    """
    Responses for all backend routes; protect real agent routes w/ pass_through
    """
    respx_mock.get("http://backend/api/v1/booking/all") % dict(
        json=["congrats you called backend /booking/all"]
    )
    respx_mock.get("http://backend/api/v1/booking/job/hello123") % dict(
        json=["congrats you called backend /booking/job/hello123"]
    )
    respx_mock.delete("http://backend/api/v1/booking/book/hello123") % dict(
        json=["congrats you called DELETE /booking/book/hello123"]
    )
    respx_mock.put("http://backend/api/v1/booking/book") % dict(
        json=["congrats you called PUT /booking/book"]
    )
    respx_mock.route(host="test").pass_through()
    return respx_mock


@mark.asyncio
async def test_job_forward(agent_client: AsyncClient):
    """
    Do we get a job from the backend?
    """
    resp = await agent_client.get("/api/v1/booking/job/hello123")
    assert resp.status_code == 200
    assert re.search(r"^congrats.*/job/hello123", resp.json()[0])


@mark.asyncio
async def test_all_forward(agent_client: AsyncClient):
    """
    Do we forward /booking/all?
    """
    resp = await agent_client.get("/api/v1/booking/all")
    assert resp.status_code == 200
    assert re.search(r"^congrats.*/booking/all", resp.json()[0])


@mark.asyncio
async def test_booking_put_forward(agent_client: AsyncClient):
    """
    Do we forward /booking/book [PUT]?
    """
    resp = await agent_client.put("/api/v1/booking/book")
    assert resp.status_code == 200
    assert re.search(r"^congrats.*/booking/book", resp.json()[0])


@mark.asyncio
async def test_booking_delete_forward(agent_client: AsyncClient):
    """
    Do we forward /booking/book [DELETE]?
    """
    resp = await agent_client.delete("/api/v1/booking/book/hello123")
    assert resp.status_code == 200
    assert re.search(r"^congrats.*/book/hello123", resp.json()[0])
