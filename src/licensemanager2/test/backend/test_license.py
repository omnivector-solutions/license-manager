"""
Tests of the /license API endpoints
"""
from fastapi import HTTPException
from httpx import AsyncClient
from pytest import mark, raises

from licensemanager2.backend import license
from licensemanager2.backend.schema import license_table
from licensemanager2.backend.storage import database
from licensemanager2.test.backend.conftest import insert_objects


def test_license_use_available():
    """
    Do we correctly calculate available on a LicenseUse object
    """
    lu = license.LicenseUse(
        product_feature="hello.world",
        total=100,
        used=81,
    )
    assert lu.available == 19


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_these_licenses(some_licenses):
    """
    Make sure we get these licenses
    """
    await insert_objects(some_licenses, license_table)
    fetched = await license._get_these_licenses(["hello.world", "cool.beans"])
    assert fetched == [
        license.LicenseUse(
            product_feature="cool.beans",
            total=11,
            used=11,
        ),
        license.LicenseUse(
            product_feature="hello.world",
            total=100,
            used=19,
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
    await insert_objects(some_licenses, license_table)
    resp = await backend_client.get("/api/v1/license/use/hello")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            product_feature="hello.dolly",
            total=80,
            used=11,
            available=69,
        ),
        dict(product_feature="hello.world", total=100, used=19, available=81),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_product_feature(backend_client: AsyncClient, some_licenses):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    resp = await backend_client.get("/api/v1/license/use/cool/beans")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            product_feature="cool.beans",
            total=11,
            used=11,
            available=0,
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all(backend_client: AsyncClient, some_licenses):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    resp = await backend_client.get("/api/v1/license/all")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(product_feature="cool.beans", total=11, used=11, available=0),
        dict(
            product_feature="hello.dolly",
            total=80,
            used=11,
            available=69,
        ),
        dict(product_feature="hello.world", total=100, used=19, available=81),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_map_bookings(some_licenses):
    """
    Do I create sql updates and inserts out of a list of bookings?
    """
    await insert_objects(some_licenses, license_table)
    lubs = [
        license.LicenseUseBooking(product_feature="cool.beans", used=19),
        license.LicenseUseBooking(product_feature="men.with_hats", used=19),
    ]
    with raises(HTTPException):
        await license.map_bookings(lubs)

    del lubs[1]
    assert await license.map_bookings(lubs) == {
        "cool.beans": license.LicenseUseBooking(product_feature="cool.beans", used=19)
    }
