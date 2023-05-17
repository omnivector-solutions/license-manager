from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.booking import BookingCRUD
from lm_backend.api.models import Booking
from lm_backend.api.schemas import BookingCreateSchema, BookingSchema, BookingUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_booking = BookingCRUD(Booking, BookingCreateSchema, BookingUpdateSchema)


@router.post(
    "/",
    response_model=BookingSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_EDIT))],
)
async def create_booking(
    booking: BookingCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new booking."""
    return await crud_booking.create(db_session=db_session, obj=booking)


@router.get(
    "/",
    response_model=List[BookingSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_VIEW))],
)
async def read_all_bookings(
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all bookings."""
    return await crud_booking.read_all(
        db_session=db_session,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/{booking_id}",
    response_model=BookingSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_VIEW))],
)
async def read_booking(booking_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a booking with associated bookings with the given id."""
    return await crud_booking.read(db_session=db_session, id=booking_id)


@router.delete(
    "/{booking_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_EDIT))],
)
async def delete_booking(booking_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a booking from the database."""
    return await crud_booking.delete(db_session=db_session, id=booking_id)
