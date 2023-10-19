from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_backend.api.models.booking import Booking
from lm_backend.permissions import Permissions


@mark.asyncio
async def test_add_booking__success(
    backend_client: AsyncClient,
    inject_security_header,
    read_object,
    create_one_job,
    create_one_feature,
):
    job_id = create_one_job[0].id
    feature_id = create_one_feature[0].id

    data = {
        "job_id": job_id,
        "feature_id": feature_id,
        "quantity": 150,
    }

    inject_security_header("owner1@test.com", Permissions.BOOKING_EDIT)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 201

    stmt = select(Booking).where(
        Booking.job_id == data["job_id"] and Booking.feature_id == data["feature_id"]
    )
    fetched = await read_object(stmt)

    assert fetched.job_id == data["job_id"]
    assert fetched.feature_id == data["feature_id"]
    assert fetched.quantity == data["quantity"]


@mark.asyncio
async def test_add_booking__fail_with_overbooking(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    create_one_feature,
):
    job_id = create_one_job[0].id
    feature_id = create_one_feature[0].id

    data = {
        "job_id": job_id,
        "feature_id": feature_id,
        "quantity": 1500,
    }

    inject_security_header("owner1@test.com", Permissions.BOOKING_EDIT)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 409


@mark.asyncio
async def test_add_booking__fail_with_overbooking_when_reserved(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_job,
    create_one_feature,
):
    job_id = create_one_job[0].id
    feature_id = create_one_feature[0].id

    data = {
        "job_id": job_id,
        "feature_id": feature_id,
        "quantity": 750,
    }

    inject_security_header("owner1@test.com", Permissions.BOOKING_EDIT)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 409


@mark.asyncio
async def test_get_all_bookings__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_bookings,
):
    inject_security_header("owner1@test.com", Permissions.BOOKING_VIEW)
    response = await backend_client.get("/lm/bookings")

    assert response.status_code == 200

    response_bookings = response.json()
    assert response_bookings[0]["job_id"] == create_bookings[0].job_id
    assert response_bookings[0]["feature_id"] == create_bookings[0].feature_id
    assert response_bookings[0]["quantity"] == create_bookings[0].quantity

    assert response_bookings[1]["job_id"] == create_bookings[1].job_id
    assert response_bookings[1]["feature_id"] == create_bookings[1].feature_id
    assert response_bookings[1]["quantity"] == create_bookings[1].quantity


@mark.asyncio
async def test_get_all_bookings__with_sort(
    backend_client: AsyncClient,
    inject_security_header,
    create_bookings,
):

    inject_security_header("owner1@test.com", Permissions.BOOKING_VIEW)
    response = await backend_client.get("/lm/bookings?sort_field=job_id&sort_ascending=false")

    assert response.status_code == 200

    response_bookings = response.json()
    assert response_bookings[0]["job_id"] == create_bookings[1].job_id
    assert response_bookings[0]["feature_id"] == create_bookings[1].feature_id
    assert response_bookings[0]["quantity"] == create_bookings[1].quantity

    assert response_bookings[1]["job_id"] == create_bookings[0].job_id
    assert response_bookings[1]["feature_id"] == create_bookings[0].feature_id
    assert response_bookings[1]["quantity"] == create_bookings[0].quantity


@mark.asyncio
async def test_get_booking__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
):
    id = create_one_booking[0].id

    inject_security_header("owner1@test.com", Permissions.BOOKING_VIEW)
    response = await backend_client.get(f"/lm/bookings/{id}")

    assert response.status_code == 200

    response_booking = response.json()
    assert response_booking["job_id"] == create_one_booking[0].job_id
    assert response_booking["feature_id"] == create_one_booking[0].feature_id
    assert response_booking["quantity"] == create_one_booking[0].quantity


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_get_booking__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
    id,
):
    inject_security_header("owner1@test.com", Permissions.BOOKING_VIEW)
    response = await backend_client.get(f"/lm/bookings/{id}")

    assert response.status_code == 404


@mark.asyncio
async def test_delete_booking__success(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
    read_object,
):
    id = create_one_booking[0].id

    inject_security_header("owner1@test.com", Permissions.BOOKING_EDIT)
    response = await backend_client.delete(f"/lm/bookings/{id}")

    assert response.status_code == 200
    stmt = select(Booking).where(Booking.id == id)
    fetch_booking = await read_object(stmt)

    assert fetch_booking is None


@mark.parametrize(
    "id",
    [
        0,
        -1,
        999999999,
    ],
)
@mark.asyncio
async def test_delete_booking__fail_with_bad_parameter(
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
    read_object,
    id,
):
    inject_security_header("owner1@test.com", Permissions.BOOKING_EDIT)
    response = await backend_client.delete(f"/lm/bookings/{id}")

    assert response.status_code == 404
