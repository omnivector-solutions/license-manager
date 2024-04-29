from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, status

from lm_api.api.cruds.booking import BookingCRUD
from lm_api.api.models.booking import Booking
from lm_api.api.schemas.booking import BookingCreateSchema, BookingSchema
from lm_api.database import SecureSession, secure_session
from lm_api.permissions import Permissions

router = APIRouter()


crud_booking = BookingCRUD(Booking)


@router.post(
    "",
    response_model=BookingSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    booking: BookingCreateSchema = Body(..., description="Booking to be created"),
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.BOOKING_CREATE)),
):
    """Create a new booking."""
    return await crud_booking.create(db_session=secure_session.session, obj=booking)


@router.get(
    "",
    response_model=List[BookingSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_bookings(
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.BOOKING_READ, commit=False)
    ),
):
    """Return all bookings."""
    return await crud_booking.read_all(
        db_session=secure_session.session,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/{booking_id}",
    response_model=BookingSchema,
    status_code=status.HTTP_200_OK,
)
async def read_booking(
    booking_id: int,
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.BOOKING_READ, commit=False)
    ),
):
    """Return a booking with associated bookings with the given id."""
    return await crud_booking.read(db_session=secure_session.session, id=booking_id)


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_booking(
    booking_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.BOOKING_DELETE)),
):
    """Delete a booking from the database."""
    return await crud_booking.delete(db_session=secure_session.session, id=booking_id)
