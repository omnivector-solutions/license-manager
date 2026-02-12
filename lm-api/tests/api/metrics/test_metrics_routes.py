from httpx import AsyncClient
from pytest import mark

from lm_api.permissions import Permissions


@mark.parametrize(
    "permission",
    [
        Permissions.METRICS_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_read_metrics__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    metrics_data,
):
    inject_security_header("owner@test.com", permission)

    response = await backend_client.get("/lm/metrics")

    assert response.status_code == 200
    body = response.text

    assert "license_total" in body
    assert "license_used" in body

    assert 'feature="abaqus"' in body
    assert 'feature="converge_super"' in body

    assert "1000.0" in body
    assert "25.0" in body
    assert "250.0" in body


@mark.parametrize(
    "permission",
    [
        Permissions.CONFIG_READ,
        Permissions.FEATURE_READ,
        Permissions.JOB_READ,
    ],
)
@mark.asyncio
async def test_read_metrics__fail_with_bad_permission(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
):
    inject_security_header("owner@test.com", permission)

    response = await backend_client.get("/lm/metrics")

    assert response.status_code == 403


@mark.asyncio
async def test_read_metrics__fail_without_auth(
    backend_client: AsyncClient,
):
    response = await backend_client.get("/lm/metrics")

    assert response.status_code == 401
