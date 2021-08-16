from httpx import AsyncClient
from pytest import fixture, mark

from lm_backend import table_schemas
from lm_backend.api import booking
from lm_backend.api_schemas import ConfigurationRow
from lm_backend.storage import database


@fixture
def some_config_rows():
    """Sample config_table row"""
    return [
        ConfigurationRow(
            product="hello",
            features=["world", "dolly"],
            license_servers=["bla"],
            license_server_type="test",
            grace_time=10,
        ),
        ConfigurationRow(
            product="cool",
            features=["beans"],
            license_servers=["bla"],
            license_server_type="test",
            grace_time=10,
        ),
    ]


@fixture
def some_booking_rows():
    """
    Some BookingRows
    """
    inserts = [
        booking.BookingRow(
            job_id="hellodollybeans",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
        ),
        booking.BookingRow(
            job_id="hellodollybeans",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
        ),
        booking.BookingRow(
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
        ),
    ]
    return inserts


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
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
        ),
    ]


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
            job_id="coolbeans",
            product_feature="cool.beans",
            booked=11,
            config_id=2,
            lead_host="host1",
            user_name="user1",
        ),
        dict(
            job_id="hellodollybeans",
            product_feature="hello.dolly",
            booked=11,
            config_id=1,
            lead_host="host1",
            user_name="user1",
        ),
        dict(
            job_id="hellodollybeans",
            product_feature="hello.world",
            booked=19,
            config_id=1,
            lead_host="host1",
            user_name="user1",
        ),
    ]
