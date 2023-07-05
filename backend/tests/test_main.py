
from fastapi import status
from httpx import AsyncClient
from pytest import mark


@mark.asyncio
async def test_health_check(backend_client: AsyncClient):
    """
    Test the health check route.

    This test ensures the API has a health check path configured properly, so
    the production and staging environments can configure the load balancing
    """

    response = await backend_client.get("/lm/health")

    assert response.status_code == status.HTTP_204_NO_CONTENT
