from unittest import mock

from fastapi import status
from httpx import AsyncClient
from pytest import mark

from lm_backend import table_schemas
from lm_backend.api import booking
from lm_backend.api_schemas import Booking, BookingFeature, BookingRow
from lm_backend.storage import database


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_get_bookings_job(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
):
    """
    Do I fetch a booking?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    resp = await backend_client.get("/api/v1/booking/job/coolbeans")
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
async def test_get_bookings_for_cluster_name(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
):
    """
    Do I fetch a booking using the cluster_name?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    booking = BookingRow(
        id=4,
        job_id="99",
        product_feature="hello.world",
        booked=1,
        lead_host="host10",
        user_name="user10",
        cluster_name="cluster2",
        config_id=2,
    )
    await insert_objects([booking], table_schemas.booking_table)
    resp = await backend_client.get("/api/v1/booking/all?cluster_name=cluster2")
    assert resp.status_code == 200
    assert resp.json() == [
        dict(
            id=4,
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
async def test_get_config_id_for_product_feature(
    some_config_rows,
    insert_objects,
):
    await insert_objects(some_config_rows, table_schemas.config_table)

    config_id = await booking.get_config_id_for_product_features("hello.world")
    assert config_id == 1


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_bookings_all(
    backend_client: AsyncClient,
    some_licenses,
    some_booking_rows,
    some_config_rows,
    insert_objects,
):
    """
    Do I fetch all the bookings in the db?
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)
    resp = await backend_client.get("/api/v1/booking/all")
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
    ]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create(backend_client, some_config_rows, some_licenses, insert_objects):
    """This test proves that a booking can be created by showing that the response status is 200."""
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=10, product_feature="hello.world")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )
    resp = await backend_client.put("/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_200_OK


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create_negative_booked_error(
    backend_client, some_config_rows, some_licenses, insert_objects
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
    resp = await backend_client.put("/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_400_BAD_REQUEST


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_create_booked_greater_than_total(
    backend_client,
    some_config_rows,
    some_licenses,
    insert_objects,
):
    """This test proves that the correct response (400) is returned when a booking
    request exceeds the total available by asserting that the response detail contains
    the string "<= total".
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    features = BookingFeature(booked=1000, product_feature="hello.world")
    booking = Booking(
        job_id=1, features=[features], lead_host="host1", user_name="user1", cluster_name="cluster1"
    )
    resp = await backend_client.put("/api/v1/booking/book", json=booking.dict())

    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "not enough" in resp.json()["detail"]


@mark.asyncio
@database.transaction(force_rollback=True)
async def test_booking_delete(
    backend_client,
    some_config_rows,
    some_licenses,
    some_booking_rows,
    insert_objects,
):
    """This test proves that the correct response is returned (200) when a booking
    is successfully deleted.
    """
    await insert_objects(some_licenses, table_schemas.license_table)
    await insert_objects(some_config_rows, table_schemas.config_table)
    await insert_objects(some_booking_rows, table_schemas.booking_table)

    resp = await backend_client.delete("/api/v1/booking/book/helloworld")
    assert resp.status_code == status.HTTP_200_OK


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
