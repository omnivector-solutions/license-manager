"""
Test the backend /api/v1 endpoints
"""
from unittest.mock import patch

from httpx import AsyncClient
from pytest import mark

from licensemanager2.backend.schema import license_table
from licensemanager2.backend.storage import database
from licensemanager2.test.backend.conftest import insert_objects


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_reset(backend_client: AsyncClient, some_licenses, ok_response):
    """
    Do I erase the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 3

    with patch("licensemanager2.backend.settings.SETTINGS.DEBUG", True):
        resp = await backend_client.put("/api/v1/reset", headers={"X-Reset": "please"})
    assert resp.status_code == 200
    assert resp.json() == ok_response.dict()

    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 0
