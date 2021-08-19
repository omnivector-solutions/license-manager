from unittest import mock

from fastapi import HTTPException, status
from httpx import AsyncClient
from pytest import mark, raises

from lm_backend.api import license
from lm_backend.api_schemas import BookingRow, LicenseUseReconcile, LicenseUseReconcileRequest
from lm_backend.storage import database
from lm_backend.table_schemas import booking_table, config_table, license_table


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
async def test_get_these_licenses(some_licenses, insert_objects):
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
    await database.execute_many(query=license_table.insert(), values=[i.dict() for i in inserts.values()])

    # try again, now 2 should be updates and 2 should be inserts
    updates, inserts = await license._find_license_updates_and_inserts(some_licenses)
    assert list(updates.keys()) == ["hello.dolly", "hello.world"]
    assert list(inserts.keys()) == ["cool.beans"]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_product(backend_client: AsyncClient, some_licenses, insert_objects):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    resp = await backend_client.get("/api/v1/license/use/hello")
    assert resp.status_code == status.HTTP_200_OK
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
async def test_licenses_product_feature(backend_client: AsyncClient, some_licenses, insert_objects):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)
    resp = await backend_client.get("/api/v1/license/use/cool/beans")
    assert resp.status_code == status.HTTP_200_OK
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
async def test_licenses_all(backend_client: AsyncClient, some_licenses, insert_objects):
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
async def test_map_bookings(some_licenses, insert_objects):
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


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_if_in_use_booking(insert_objects, some_licenses, some_config_rows, some_booking_rows):
    """
    Make sure the given LicenseUseReconcileRequest gets deleted only if the pair booked, lead_host,
    user_name and product_feature exists in the booking table.
    """
    await insert_objects(some_config_rows, config_table)
    await insert_objects(some_booking_rows, booking_table)
    await insert_objects(some_licenses, license_table)

    used_licenses = [
        {"booked": 19, "lead_host": "host1", "user_name": "user1"},
        {"booked": 11, "lead_host": "host1", "user_name": "user1"},
        {"booked": 12, "lead_host": "host1", "user_name": "user1"},
        {"booked": 13, "lead_host": "host1", "user_name": "user1"},
        {"booked": 14, "lead_host": "host1", "user_name": "user1"},
    ]
    license_reconcile_request = LicenseUseReconcileRequest(
        used=19, product_feature="hello.world", total=100, used_licenses=used_licenses
    )

    await license._delete_if_in_use_booking(license_reconcile_request)

    booking_rows = [BookingRow.parse_obj(x) for x in await database.fetch_all(booking_table.select())]
    assert len(booking_rows) == len(some_booking_rows) - 1  # i.e. one got deleted


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_delete_if_in_use_booking_empty(
    insert_objects, some_licenses, some_config_rows, some_booking_rows
):
    """
    Check if the function works well given a used_liceses empty and don't delete anything from the
    booking_table.
    """
    await insert_objects(some_config_rows, config_table)
    await insert_objects(some_booking_rows, booking_table)
    await insert_objects(some_licenses, license_table)

    used_licenses = []
    license_reconcile_request = LicenseUseReconcileRequest(
        used=19, product_feature="hello.world", total=100, used_licenses=used_licenses
    )

    await license._delete_if_in_use_booking(license_reconcile_request)

    booking_rows = [BookingRow.parse_obj(x) for x in await database.fetch_all(booking_table.select())]
    assert len(booking_rows) == len(some_booking_rows)


@mark.asyncio
@mock.patch("lm_backend.api.license._delete_if_in_use_booking")
@database.transaction(force_rollback=True)
async def test_clean_up_in_use_booking_conversion(delete_in_use_mock: mock.AsyncMock):
    """
    Check if the _clean_up_in_use_booking actually converts the data type and calls the
    _delete_if_in_use_booking.
    """
    used_licenses = [
        {"booked": 19, "lead_host": "host1", "user_name": "user1"},
        {"booked": 11, "lead_host": "host1", "user_name": "user1"},
        {"booked": 12, "lead_host": "host1", "user_name": "user1"},
        {"booked": 13, "lead_host": "host1", "user_name": "user1"},
        {"booked": 14, "lead_host": "host1", "user_name": "user1"},
    ]
    license_reconcile_requests = [
        LicenseUseReconcileRequest(
            used=19, product_feature="hello.world", total=100, used_licenses=used_licenses
        ),
        LicenseUseReconcileRequest(
            used=11, product_feature="hello.dolly", total=100, used_licenses=used_licenses
        ),
    ]

    license_reconciles = await license._clean_up_in_use_booking(license_reconcile_requests)
    assert len(license_reconciles) == len(license_reconcile_requests)
    assert isinstance(license_reconciles[0], LicenseUseReconcile)
    assert isinstance(license_reconciles[1], LicenseUseReconcile)
    assert delete_in_use_mock.await_count == 2


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_changes_clean_up_in_use_bookings(
    insert_objects, some_licenses, some_config_rows, some_booking_rows, backend_client
):
    """
    Make sure the /reconcile endpoint correct handle the in use cleanup.
    """
    await insert_objects(some_config_rows, config_table)
    await insert_objects(some_booking_rows, booking_table)
    await insert_objects(some_licenses, license_table)

    used_licenses = [
        {"booked": 19, "lead_host": "host1", "user_name": "user1"},
    ]
    license_reconcile_request = LicenseUseReconcileRequest(
        used=19, product_feature="hello.world", total=100, used_licenses=used_licenses
    )

    response = await backend_client.patch(
        "/api/v1/license/reconcile", json=[license_reconcile_request.dict()]
    )
    assert response.status_code == status.HTTP_200_OK

    booking_rows = [BookingRow.parse_obj(x) for x in await database.fetch_all(booking_table.select())]
    assert len(booking_rows) == len(some_booking_rows) - 1  # i.e. one got deleted
