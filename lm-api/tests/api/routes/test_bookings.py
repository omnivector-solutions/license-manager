from httpx import AsyncClient
from pytest import mark
from sqlalchemy import select

from lm_api.api.models.booking import Booking
from lm_api.permissions import Permissions


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_booking__success(
    permission,
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

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 201

    stmt = select(Booking).where(
        Booking.job_id == data["job_id"] and Booking.feature_id == data["feature_id"]
    )
    fetched = await read_object(stmt)

    assert fetched.job_id == data["job_id"]
    assert fetched.feature_id == data["feature_id"]
    assert fetched.quantity == data["quantity"]


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_booking__fail_with_overbooking(
    permission,
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

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 409


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_CREATE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_add_booking__fail_with_overbooking_when_reserved(
    permission,
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

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.post("/lm/bookings", json=data)

    assert response.status_code == 409


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_bookings__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_bookings,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/bookings")

    assert response.status_code == 200

    response_bookings = response.json()
    assert response_bookings[0]["job_id"] == create_bookings[0].job_id
    assert response_bookings[0]["feature_id"] == create_bookings[0].feature_id
    assert response_bookings[0]["quantity"] == create_bookings[0].quantity

    assert response_bookings[1]["job_id"] == create_bookings[1].job_id
    assert response_bookings[1]["feature_id"] == create_bookings[1].feature_id
    assert response_bookings[1]["quantity"] == create_bookings[1].quantity


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_all_bookings__with_sort(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_bookings,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get("/lm/bookings?sort_field=job_id&sort_ascending=false")

    assert response.status_code == 200

    response_bookings = response.json()
    assert response_bookings[0]["job_id"] == create_bookings[1].job_id
    assert response_bookings[0]["feature_id"] == create_bookings[1].feature_id
    assert response_bookings[0]["quantity"] == create_bookings[1].quantity

    assert response_bookings[1]["job_id"] == create_bookings[0].job_id
    assert response_bookings[1]["feature_id"] == create_bookings[0].feature_id
    assert response_bookings[1]["quantity"] == create_bookings[0].quantity


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_READ,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_get_booking__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
):
    id = create_one_booking[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/bookings/{id}")

    assert response.status_code == 200

    response_booking = response.json()
    assert response_booking["job_id"] == create_one_booking[0].job_id
    assert response_booking["feature_id"] == create_one_booking[0].feature_id
    assert response_booking["quantity"] == create_one_booking[0].quantity


@mark.parametrize(
    "id, permission",
    [
        (0, Permissions.BOOKING_READ),
        (-1, Permissions.BOOKING_READ),
        (999999999, Permissions.BOOKING_READ),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_get_booking__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
):
    inject_security_header("owner1@test.com", permission)
    response = await backend_client.get(f"/lm/bookings/{id}")

    assert response.status_code == 404


@mark.parametrize(
    "permission",
    [
        Permissions.BOOKING_DELETE,
        Permissions.ADMIN,
    ],
)
@mark.asyncio
async def test_delete_booking__success(
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
    read_object,
):
    id = create_one_booking[0].id

    inject_security_header("owner1@test.com", permission)
    response = await backend_client.delete(f"/lm/bookings/{id}")

    assert response.status_code == 200
    stmt = select(Booking).where(Booking.id == id)
    fetch_booking = await read_object(stmt)

    assert fetch_booking is None


@mark.parametrize(
    "id, permission",
    [
        (0, Permissions.BOOKING_DELETE),
        (-1, Permissions.BOOKING_DELETE),
        (999999999, Permissions.BOOKING_DELETE),
        (0, Permissions.ADMIN),
        (-1, Permissions.ADMIN),
        (999999999, Permissions.ADMIN),
    ],
)
@mark.asyncio
async def test_delete_booking__fail_with_bad_parameter(
    id,
    permission,
    backend_client: AsyncClient,
    inject_security_header,
    create_one_booking,
    read_object,
):
    inject_security_header("owner1@test.com", permission.BOOKING_DELETE)
    response = await backend_client.delete(f"/lm/bookings/{id}")

    assert response.status_code == 404
