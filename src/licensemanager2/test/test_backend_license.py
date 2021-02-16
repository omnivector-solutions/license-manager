"""
Tests of the /license API endpoints
"""
from unittest.mock import patch

from httpx import AsyncClient
from pytest import fixture, mark

from licensemanager2.backend import license
from licensemanager2.backend.schema import license_table
from licensemanager2.backend.storage import database


@fixture
def some_licenses():
    """
    Some LicenseUse bookings
    """
    LUR = license.LicenseUseReconcile
    inserts = [
        LUR(
            product_feature="hello.world",
            total=100,
            booked=19,
        ),
        LUR(
            product_feature="hello.dolly",
            total=80,
            booked=11,
        ),
        LUR(
            product_feature="cool.beans",
            total=11,
            booked=11,
        ),
    ]
    return inserts


async def insert_licenses(inserts):
    """
    Perform a database insertion for the licenses passed as the argument
    """
    await database.execute_many(
        query=license_table.insert(), values=[lu.dict() for lu in inserts]
    )
    objects = await database.fetch_all(license_table.select())
    assert len(objects) == 3, "More than 3 licenses, maybe data was left in the db"
    return [license.LicenseUse.parse_obj(o) for o in objects]


def test_license_use_available():
    """
    Do we correctly calculate available on a LicenseUse object
    """
    lu = license.LicenseUse(
        product_feature="hello.world",
        total=100,
        booked=81,
    )
    assert lu.available == 19


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_these_licenses(some_licenses):
    """
    Make sure we get these licenses
    """
    await insert_licenses(some_licenses)
    fetched = await license._get_these_licenses(["hello.world", "cool.beans"])
    assert fetched == [
        license.LicenseUse(
            product_feature="cool.beans",
            total=11,
            booked=11,
        ),
        license.LicenseUse(
            product_feature="hello.world",
            total=100,
            booked=19,
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_find_license_updates_and_inserts(some_licenses):
    """
    Do we correctly match a list of objects against the database and
    determine which are new and which are updating?
    """
    # initially, everything should be an insert
    updates, inserts = await license._find_license_updates_and_inserts(some_licenses)
    assert len(updates) == 0
    assert len(inserts) == 3

    # let's insert 2 of the three
    del inserts["cool.beans"]
    await database.execute_many(
        query=license_table.insert(), values=[i.dict() for i in inserts.values()]
    )

    # try again, now 2 should be updates and 2 should be inserts
    updates, inserts = await license._find_license_updates_and_inserts(some_licenses)
    assert list(updates.keys()) == ["hello.dolly", "hello.world"]
    assert list(inserts.keys()) == ["cool.beans"]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_product(backend_client: AsyncClient, some_licenses):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_licenses(some_licenses)
    resp = await backend_client.get("/api/v1/license/use/hello")
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
@database.transaction(force_rollback=True)
async def test_licenses_product_feature(backend_client: AsyncClient, some_licenses):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_licenses(some_licenses)
    resp = await backend_client.get("/api/v1/license/use/cool/beans")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            product_feature="cool.beans",
            total=11,
            booked=11,
            available=0,
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all(backend_client: AsyncClient, some_licenses):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_licenses(some_licenses)
    resp = await backend_client.get("/api/v1/license/all")
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


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_reset(backend_client: AsyncClient, some_licenses, ok_response):
    """
    Do I erase the licenses in the db?
    """
    await insert_licenses(some_licenses)
    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 3

    with patch("licensemanager2.backend.settings.SETTINGS.DEBUG", True):
        resp = await backend_client.put(
            "/api/v1/license/reconcile", headers={"X-Reconcile-Reset": "please"}
        )
    assert resp.status_code == 200
    assert resp.json() == ok_response.dict()

    count = await database.fetch_all("SELECT COUNT(*) FROM license")
    assert count[0][0] == 0
