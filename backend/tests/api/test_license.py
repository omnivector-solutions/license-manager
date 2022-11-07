from unittest import mock

from fastapi import HTTPException, status
from httpx import AsyncClient
from pytest import mark, raises

from lm_backend.api import license
from lm_backend.api.permissions import Permissions
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


def test_license_use_with_booking_calculate_available():
    """
    Do we correctly calculate available on a LicenseUseWithBooking object?
    """
    lu = license.LicenseUseWithBooking(product_feature="hello.world", total=100, used=81, booked=10)
    assert lu.available == 9


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
    assert len(inserts) == 4

    # let's insert 3 of the four
    del inserts["cool.beans"]
    await database.execute_many(query=license_table.insert(), values=[i.dict() for i in inserts.values()])

    # try again, now 3 should be updates and 1 should be inserts
    updates, inserts = await license._find_license_updates_and_inserts(some_licenses)
    assert list(updates.keys()) == ["hello.dolly", "hello.world", "limited.license"]
    assert list(inserts.keys()) == ["cool.beans"]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_product__success(
    backend_client: AsyncClient,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/use/hello")
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
async def test_licenses_product__fail_on_bad_permission(
    backend_client: AsyncClient,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """
    Do I return a 401 or 403 if permissions are missing or invalid?
    """
    await insert_objects(some_licenses, license_table)

    # No Permission
    resp = await backend_client.get("/lm/api/v1/license/use/hello")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/license/use/hello")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_product_feature__success(
    backend_client: AsyncClient,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/use/cool/beans")
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
async def test_licenses_product_feature__fail_on_bad_permission(
    backend_client: AsyncClient,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """
    Do I return a 401 or 403 if permissions are missing or invalid?
    """
    await insert_objects(some_licenses, license_table)

    # No Permission
    resp = await backend_client.get("/lm/api/v1/license/use/cool/beans")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Invalid Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/license/use/cool/beans")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_with_booking_all__success(
    backend_client: AsyncClient, some_licenses, insert_objects, inject_security_header
):
    """
    Do I fetch and order the licenses with booking in the db?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/complete/all")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(product_feature="cool.beans", total=11, used=11, booked=0, available=0),
        dict(
            product_feature="hello.dolly",
            total=80,
            used=11,
            booked=0,
            available=69,
        ),
        dict(product_feature="hello.world", total=100, used=19, booked=0, available=81),
        dict(product_feature="limited.license", total=50, used=40, booked=0, available=10),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all__success(
    backend_client: AsyncClient, some_licenses, insert_objects, inject_security_header
):
    """
    Do I fetch and order the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/all")
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
        dict(product_feature="limited.license", total=50, used=40, available=10),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all__with_search(
    backend_client: AsyncClient, some_licenses, insert_objects, inject_security_header
):
    """
    Do I fetch and filter by the supplied search term the licenses in the db?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/all?search=dolly")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            product_feature="hello.dolly",
            total=80,
            used=11,
            available=69,
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all__with_sort(
    backend_client: AsyncClient, some_licenses, insert_objects, inject_security_header
):
    """
    Do I fetch and order the licenses in the db by the supplied sort params?
    """
    await insert_objects(some_licenses, license_table)

    inject_security_header("owner1", Permissions.LICENSE_VIEW)
    resp = await backend_client.get("/lm/api/v1/license/all?sort_field=total&sort_ascending=false")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(product_feature="hello.world", total=100, used=19, available=81),
        dict(
            product_feature="hello.dolly",
            total=80,
            used=11,
            available=69,
        ),
        dict(product_feature="limited.license", total=50, used=40, available=10),
        dict(product_feature="cool.beans", total=11, used=11, available=0),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_licenses_all__fail_on_bad_permission(
    backend_client: AsyncClient, some_licenses, insert_objects, inject_security_header
):
    """
    Do I return a 401 or 403 if permissions are missing or invalid?
    """
    await insert_objects(some_licenses, license_table)

    # No Permission
    # Invalid Permission
    resp = await backend_client.get("/lm/api/v1/license/all")
    assert resp.status_code == 401

    # Invalid Permission
    inject_security_header("owner1", "invalid_permission")
    resp = await backend_client.get("/lm/api/v1/license/all")
    assert resp.status_code == 403


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

    booking_rows = await database.fetch_all(booking_table.select())
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

    booking_rows = await database.fetch_all(booking_table.select())
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
            used=11, product_feature="hello.dolly", total=80, used_licenses=used_licenses
        ),
    ]

    license_reconciles = await license._clean_up_in_use_booking(license_reconcile_requests)
    assert len(license_reconciles) == len(license_reconcile_requests)
    assert isinstance(license_reconciles[0], LicenseUseReconcile)
    assert isinstance(license_reconciles[1], LicenseUseReconcile)
    assert delete_in_use_mock.await_count == 2


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_changes_clean_up_in_use_bookings__success(
    insert_objects,
    some_licenses,
    some_config_rows,
    some_booking_rows,
    backend_client,
    inject_security_header,
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

    inject_security_header("owner1", Permissions.LICENSE_EDIT)
    response = await backend_client.patch(
        "/lm/api/v1/license/reconcile", json=[license_reconcile_request.dict()]
    )
    assert response.status_code == status.HTTP_200_OK

    booking_rows = await database.fetch_all(booking_table.select())
    assert len(booking_rows) == len(some_booking_rows) - 1  # i.e. one got deleted


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_reconcile_changes_clean_up_in_use_bookings__fail_on_bad_permission(
    insert_objects,
    some_licenses,
    some_config_rows,
    some_booking_rows,
    backend_client,
    inject_security_header,
):
    """
    Do I return a 401 or 403 if permissions are missing or invalid?
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

    # No Permission
    response = await backend_client.patch(
        "/lm/api/v1/license/reconcile", json=[license_reconcile_request.dict()]
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Invalid Permission
    inject_security_header("owner1", "invalid-permission")
    response = await backend_client.patch(
        "/lm/api/v1/license/reconcile", json=[license_reconcile_request.dict()]
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
