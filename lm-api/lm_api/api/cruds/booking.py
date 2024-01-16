"""Booking CRUD class for SQLAlchemy models."""
from fastapi import HTTPException
from loguru import logger
from sqlalchemy import func, insert, literal, select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.booking import Booking
from lm_api.api.models.feature import Feature
from lm_api.api.schemas.booking import BookingCreateSchema


class BookingCRUD(GenericCRUD):
    """Booking CRUD module to overload create method, preventing the overbooking issue."""

    async def create(self, db_session: AsyncSession, obj=BookingCreateSchema) -> Booking:
        """
        Create a new booking.

        Use a somewhat complex logic to check if a booking can be made and insert it in one query. In this
        case, implement the `INSERT columns FROM select_query WHERE EXISTS (SELECT subquery)` SQL paradigm
        using SQLAlchemy query API. A  booking will only be created if there are enough licenses available
        to make the booking.

        To determine if a booking can be made, we check if the amount of licenses already booked, the licenses
        in use, the licenses reserved and the amount requested, are smaller or equal the license total.
        """

        # CTE used to provide the request values to the insert/select query.
        vars_cte = select(
            literal(obj.feature_id).label("feature_id"),
            literal(obj.job_id).label("job_id"),
            literal(obj.quantity).label("quantity"),
        ).cte("vars")

        # Subquery to determine if there are enough licenses to be booked
        exists_subquery = (
            select(Feature.id)
            .select_from(Feature)
            .join(Booking, Feature.id == Booking.feature_id, isouter=True)
            .where(Feature.id == obj.feature_id)
            .group_by(Feature.id)
            .having(
                func.sum(func.coalesce(Booking.quantity, 0))
                + func.max(Feature.used)
                + func.max(Feature.reserved)
                + obj.quantity
                <= func.max(Feature.total)
            )
        ).exists()

        # Composite query using the CTE and subquery to atomically check-then-set the new booking
        insert_query = (
            insert(Booking)
            .from_select(
                ["job_id", "feature_id", "quantity"],
                select(
                    vars_cte.c.job_id,
                    vars_cte.c.feature_id,
                    vars_cte.c.quantity,
                )
                .select_from(vars_cte)
                .where(exists_subquery),
            )
            .returning(Booking)
        )

        try:
            result = await db_session.execute(insert_query)
            db_obj = result.scalars().one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Object could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=409, detail="Not enough licenses available.")

        return db_obj
