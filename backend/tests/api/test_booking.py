from datetime import datetime
from unittest import mock

from fastapi import status
from httpx import AsyncClient
from pytest import mark, raises

from lm_backend import table_schemas
from lm_backend.api import booking
from lm_backend.api_schemas import Booking, BookingFeature, BookingRow, ConfigurationRow, LicenseUseReconcile
from lm_backend.constants import LicenseServerType, Permissions
from lm_backend.exceptions import LicenseManagerFeatureConfigurationIncorrect
from lm_backend.storage import database


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings__by_id(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
    time_frame,
):
    """
    Do I fetch a booking?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    with time_frame() as window:
        await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get(f"/lm/api/v1/booking/{1}")

    assert resp.status_code == 200
    resp_data = resp.json()

    created_at = datetime.strptime(resp_data.pop("created_at"), "%Y-%m-%dT%H:%M:%S")
    assert created_at in window

    assert resp_data == dict(
        id=1,
        job_id="helloworld",
        product_feature="hello.world",
        booked=19,
        config_id=1,
        lead_host="host1",
        user_name="user1",
        cluster_name="cluster1",
        config_name="HelloDolly",
    )


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings_job__success(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch a booking?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get("/lm/api/v1/booking/job/coolbeans")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings_job__fails_with_bad_permission(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I give a 401 with an invalid or missing permission?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    # No permission
    resp = await backend_client.get("/lm/api/v1/booking/job/coolbeans")
    assert resp.status_code == 401

    # Bad permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/booking/job/coolbeans")
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings_for_cluster_name__success(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch a booking using the cluster_name?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    booking = BookingRow(
        id=5,
        job_id="99",
        product_feature="hello.world",
        booked=1,
        lead_host="host10",
        user_name="user10",
        cluster_name="cluster2",
        config_id=2,
    )
    await insert_objects([booking], table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get("/lm/api/v1/booking/all?cluster_name=cluster2")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=5,
            job_id="99",
            product_feature="hello.world",
            booked=1,
            config_id=2,
            lead_host="host10",
            user_name="user10",
            cluster_name="cluster2",
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings__fails_on_bad_permission(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fail with bad or missing permissions?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    booking = BookingRow(
        id=5,
        job_id="99",
        product_feature="hello.world",
        booked=1,
        lead_host="host10",
        user_name="user10",
        cluster_name="cluster2",
        config_id=2,
    )
    await insert_objects([booking], table_schemas.booking_table)

    # No Permission
    resp = await backend_client.get("/lm/api/v1/booking/all?cluster_name=cluster2")
    assert resp.status_code == 401

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.get("/lm/api/v1/booking/all?cluster_name=cluster2")
    assert resp.status_code == 403


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_config_id_for_product_feature(
    some_config_rows,
    insert_objects,
):
    await insert_objects(some_config_rows, table_schemas.config_table)

    config_id = await booking.get_config_id_for_product_features("hello.world")
    assert config_id == 1


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_bookings_all__basic(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch all the bookings in the db?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get("/lm/api/v1/booking/all")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=1,
            job_id="helloworld",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=4,
            job_id="limitedlicense",
            product_feature="limited.license",
            booked=40,
            config_id=3,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_bookings_all__with_search(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch all the bookings and apply search? Do I ignore search if cluster_name param provided?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get("/lm/api/v1/booking/all?search=dolly")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]

    resp = await backend_client.get("/lm/api/v1/booking/all?search=dolly&cluster_name=cluster1")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=1,
            job_id="helloworld",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=4,
            job_id="limitedlicense",
            product_feature="limited.license",
            booked=40,
            config_id=3,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_bookings_all__with_sort(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
    inject_security_header,
):
    """
    Do I fetch all the bookings sorted by provided sort field?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_VIEW)
    resp = await backend_client.get("/lm/api/v1/booking/all?sort_field=job_id")

    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=3,
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=2,
            job_id="hellodolly",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=1,
            job_id="helloworld",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
        dict(
            id=4,
            job_id="limitedlicense",
            product_feature="limited.license",
            booked=40,
            config_id=3,
            lead_host="host1",
            user_name="user1",
            cluster_name="cluster1",
        ),
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create__success(
    backend_client,
    some_config_rows,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """This test proves that a booking can be created by showing that the response status is 200."""
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=10, product_feature="hello.world")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )

    inject_security_header("owner1", Permissions.BOOKING_EDIT)
    resp = await backend_client.put("/lm/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_200_OK


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create__fail_on_bad_permission(
    backend_client,
    some_config_rows,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """
    This test proves that a 401 or 403 will be returend by the endpoint if the supplied
    auth token is missiong or invalid.
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=10, product_feature="hello.world")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )

    # No Permission
    resp = await backend_client.put("/lm/api/v1/booking/book", json=booking.dict())
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Bad Permission
    inject_security_header("owner1", "bad-permission")
    resp = await backend_client.put("/lm/api/v1/booking/book", json=booking.dict())
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create_negative_booked_error(
    backend_client,
    some_config_rows,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """This test proves that a 400 response code is returned when a `-` (negative) booking creation is
    attempted by checking the response code of a booking request containing a negative booking.
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=-1, product_feature="hello.world")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )

    inject_security_header("owner1", Permissions.BOOKING_EDIT)
    resp = await backend_client.put("/lm/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create_booked_greater_than_limit(
    backend_client,
    some_config_rows,
    some_licenses,
    insert_objects,
    inject_security_header,
):
    """This test proves that the correct response (400) is returned when a booking
    request exceeds the limit of licenses  available by asserting that the response
    detail contains the string "<= total".
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=5, product_feature="limited.license")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )
    inject_security_header("owner1", Permissions.BOOKING_EDIT)
    resp = await backend_client.put("/lm/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not enough" in resp.json()["detail"]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_delete__success(
    backend_client,
    some_config_rows,
    some_licenses,
    some_booking_rows,
    insert_objects,
    inject_security_header,
):
    """This test proves that the correct response is returned (200) when a booking
    is successfully deleted.
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    inject_security_header("owner1", Permissions.BOOKING_EDIT)
    resp = await backend_client.delete("/lm/api/v1/booking/book/helloworld")
    assert resp.status_code == status.HTTP_200_OK


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_delete__fail_on_bad_permissions(
    backend_client,
    some_config_rows,
    some_licenses,
    some_booking_rows,
    insert_objects,
    inject_security_header,
):
    """
    This test proves that a 401 or 403 response is returned when the auth token
    is missing or invalid.
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    # No Permission
    resp = await backend_client.delete("/lm/api/v1/booking/book/helloworld")
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Bad Permission
    inject_security_header("owner1", "invalid-permission")
    resp = await backend_client.delete("/lm/api/v1/booking/book/helloworld")
    assert resp.status_code == status.HTTP_403_FORBIDDEN


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_is_booking_available_not_available(
    some_config_rows,
    some_licenses,
    some_booking_rows,
    insert_objects,
):
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    features = BookingFeature(booked=100, product_feature="hello.world")
    booking_row = Booking(
        job_id="new", features=[features], lead_host="host1", user_name="user2", cluster_name="cluster1"
    )

    assert await booking._is_booking_available(booking_row) is False


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_is_booking_available(
    some_config_rows,
    some_licenses,
    insert_objects,
):
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=81, product_feature="hello.world")
    booking_row = Booking(
        job_id="new", features=[features], lead_host="host1", user_name="user2", cluster_name="cluster1"
    )

    assert await booking._is_booking_available(booking_row) is True


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_limit_for_booking_feature(
    some_config_rows,
    some_licenses,
    insert_objects,
):
    """Test that the correct limit is returned for a given feature."""
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)

    assert await booking._get_limit_for_booking_feature("hello.world") == 100
    assert await booking._get_limit_for_booking_feature("hello.dolly") == 80
    assert await booking._get_limit_for_booking_feature("cool.beans") == 11
    assert await booking._get_limit_for_booking_feature("limited.license") == 40


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_limit_for_booking_feature__without_limit_specified(insert_objects):
    """Test that the total is used when the limit is not in the feature configuration."""
    await insert_objects(
        [
            ConfigurationRow(
                id=1,
                name="NotALimitedLicense",
                product="notlimited",
                features='{"license": {"total": 50}}',
                license_servers=["bla"],
                license_server_type=LicenseServerType.FLEXLM,
                grace_time=10,
                client_id="cluster-staging",
            )
        ],
        table_schemas.config_table,
    )

    assert await booking._get_limit_for_booking_feature("notlimited.license") == 50


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_limit_for_booking_feature__fallback_to_old_format(insert_objects):
    """Test that the total is used as limit when the feature configuration is in the old format."""
    await insert_objects(
        [
            ConfigurationRow(
                id=1,
                name="OldFormatLicense",
                product="old",
                features='{"license": 50}',
                license_servers=["bla"],
                license_server_type=LicenseServerType.FLEXLM,
                grace_time=10,
                client_id="cluster-staging",
            )
        ],
        table_schemas.config_table,
    )

    assert await booking._get_limit_for_booking_feature("old.license") == 50


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_limit_for_booking_feature__raise_exception_incorrect_feature(insert_objects):
    """Test that an exception is raised if the feature doesn't have the total."""
    await insert_objects(
        [
            ConfigurationRow(
                id=1,
                name="IncorrectFormatLicense",
                product="incorrect",
                features='{"license": {"bla": 123}}',
                license_servers=["bla"],
                license_server_type=LicenseServerType.FLEXLM,
                grace_time=10,
                client_id="cluster-staging",
            )
        ],
        table_schemas.config_table,
    )

    with raises(LicenseManagerFeatureConfigurationIncorrect):
        await booking._get_limit_for_booking_feature("incorrect.license")
