from unittest.mock import patch

from httpx import AsyncClient
from pytest import mark

from lm_backend.storage import database
from lm_backend.table_schemas import license_table


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_reset(backend_client: AsyncClient, some_licenses, insert_objects):
    """
    Do I erase the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 3

    with patch("lm_backend.debug.settings.DEBUG", True):
        resp = await backend_client.put("/api/v1/reset", headers={"X-Reset": "please"})
    assert resp.status_code == 200

    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 0
