from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, func, literal, and_

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Booking, Feature, Inventory
from lm_backend.api.schemas import BookingCreateSchema, BookingSchema, BookingUpdateSchema
from lm_backend.database import get_session
from lm_backend.permissions import Permissions
from lm_backend.security import guard

router = APIRouter()


crud_booking = GenericCRUD(Booking, BookingCreateSchema, BookingUpdateSchema)


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
    """Create a new booking.

    Use a somewhat complex logic to check if a booking can be made and insert it in one query. In this case,
    implement the `INSERT columns FROM select_query WHERE EXISTS (SELECT subquery)` SQL paradigm using
    SQLAlchemy query API. A  booking will only be created if there are enough licenses available to make the
    booking.
    """

    # CTE used to provide the request values to the insert/select query.
    vars_cte = select(
        literal(booking.feature_id).label("feature_id"),
        literal(booking.job_id).label("job_id"),
        literal(booking.quantity).label("quantity"),
    ).cte("vars")

    # Subquery to determine if there are enough licenses to be booked
    exists_subquery = (
        select(Feature.id)
        .select_from(Feature)
        .join(Booking, and_(Feature.id == Booking.feature_id, Booking.feature_id == booking.feature_id))
        .join(Inventory, Feature.id == Inventory.feature_id)
        .group_by(Feature.id)
        .having(
            func.sum(Booking.quantity)
            + func.max(Inventory.used)
            + booking.quantity
            < func.max(Inventory.total)
        )
    ).exists()

    # Composite query using the CTE and subquery to atomically check-then-set the new booking
    insert_query = insert(Booking).from_select(
        ["job_id", "feature_id", "quantity"],
        select(
            vars_cte.c.job_id,
            vars_cte.c.feature_id,
            vars_cte.c.quantity,
        ).select_from(
            vars_cte
        ).where(
            exists_subquery
        ),
    ).returning(Booking)

    async with db_session.begin():
        try:
            result = await db_session.execute(insert_query)
            db_obj = result.scalars().one_or_none()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Object could not be read: {e}")

    if db_obj is None:
        raise HTTPException(status_code=409, detail="Not enough licenses available")

    return db_obj


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
    await crud_booking.delete(db_session=db_session, id=booking_id)
    return {"message": "Booking deleted successfully"}
