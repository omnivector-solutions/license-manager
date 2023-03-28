"""CRUD operations for bookings."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.booking import BookingCreateSchema, BookingSchema, BookingUpdateSchema
from lm_backend.models.booking import Booking


class BookingCRUD:
    """
    CRUD operations for bookings.
    """

    async def create(self, db_session: AsyncSession, booking: BookingCreateSchema) -> BookingSchema:
        """
        Add a new booking to the database.
        Returns the newly created booking.
        """
        new_booking = Booking(**booking.dict())
        try:
            await db_session.add(new_booking)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Booking could not be created")
        return BookingSchema.from_orm(new_booking)

    async def read(self, db_session: AsyncSession, booking_id: int) -> Optional[BookingSchema]:
        """
        Read a booking with the given id.
        Returns the booking.
        """
        query = await db_session.execute(select(Booking).filter(Booking.id == booking_id))
        db_booking = query.scalars().one_or_none()

        if db_booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")

        return BookingSchema.from_orm(db_booking.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[BookingSchema]:
        """
        Read all bookings.
        Returns a list of bookings.
        """
        query = await db_session.execute(select(Booking))
        db_bookings = query.scalars().all()
        return [BookingSchema.from_orm(db_booking) for db_booking in db_bookings]

    async def update(
        self, db_session: AsyncSession, booking_id: int, booking_update: BookingUpdateSchema
    ) -> Optional[BookingSchema]:
        """
        Update a booking in the database.
        Returns the updated booking.
        """
        query = await db_session.execute(select(Booking).filter(Booking.id == booking_id))
        db_booking = query.scalar_one_or_none()

        if db_booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")

        for field, value in booking_update:
            setattr(db_booking, field, value)

        await db_session.commit()
        await db_session.refresh(db_booking)
        return BookingSchema.from_orm(db_booking)

    async def delete(self, db_session: AsyncSession, booking_id: int) -> bool:
        """
        Delete a booking from the database.
        """
        query = await db_session.execute(select(Booking).filter(Booking.id == booking_id))
        db_booking = query.scalars().one_or_none()

        if db_booking is None:
            raise HTTPException(status_code=404, detail="Booking not found")
        try:
            db_session.delete(db_booking)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Booking could not be deleted")
