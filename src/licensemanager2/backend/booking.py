"""
License objects and routes
"""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.sql import delete, func, select

from licensemanager2.backend.schema import booking_table
from licensemanager2.backend.storage import database
from licensemanager2.common_api import OK
from licensemanager2.compat import INTEGRITY_CHECK_EXCEPTIONS


PRODUCT_FEATURE_RX = r"^.+?\..+$"


router_booking = APIRouter()


class BookingFeature(BaseModel):
    """
    One booked count for a single product.feature in a booking
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    booked: int

    class Config:
        orm_mode = True


class Booking(BaseModel):
    """
    A booking for a jobid with a list of the features it requests
    """

    job_id: str
    features: List[BookingFeature]

    class Config:
        orm_mode = True


class BookingRow(BaseModel):
    """
    A flattened booking, suitable to be inserted into the database
    """

    job_id: str
    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    booked: int

    class Config:
        orm_mode = True


@router_booking.get("/all", response_model=List[BookingRow])
async def bookings_all():
    """
    All license counts we are tracking
    """
    query = booking_table.select().order_by(
        booking_table.c.job_id, booking_table.c.product_feature
    )
    return await database.fetch_all(query)


@router_booking.get("/job/{job_id}", response_model=List[BookingRow])
async def bookings_job(job_id: str):
    """
    All bookings of a particular job
    """
    query = (
        booking_table.select()
        .where(booking_table.c.job_id == job_id)
        .order_by(booking_table.c.product_feature)
    )
    return await database.fetch_all(query)


@database.transaction()
@router_booking.put("/book", response_model=OK)
async def create_booking(booking: Booking):
    """
    Put a LicenseUse booking object in the database, reserving some tokens

    If an existing product_feature exists for this, update it by incrementing `booked',
    otherwise create it.

    An error occurs if the new total for `booked` exceeds `total`
    """
    inserts = []
    for feature in booking.features:
        inserts.append(
            BookingRow(
                job_id=booking.job_id,
                product_feature=feature.product_feature,
                booked=feature.booked,
            )
        )

    try:
        await database.execute_many(
            query=booking_table.insert(), values=[i.dict() for i in inserts]
        )
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Couldn't book {booking.job_id}, it is already booked"
            ),
        )

    # FIXME("update the license table")

    count_ = await database.fetch_one(
        select([func.count()]).where(booking_table.c.job_id == booking.job_id).select_from(booking_table)
    )
    count = count_[0]

    return OK(message=f"inserted {booking.job_id} to book {count} product features")


@database.transaction()
@router_booking.delete("/book/{job_id}", response_model=OK)
async def delete_booking(job_id: str):
    """
    Deduct tokens from a LicenseUse booking in the database

    It is an error to use this method with a product_feature that isn't yet in the database.
    Use reconcile or booking[PUT] to create the target first.

    An error occurs if the new total for `booked` is < 0
    """
    exists = await bookings_job(job_id)
    if not exists:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Couldn't find booking {job_id} to delete"
            ),
        )
    q = delete(booking_table).where(booking_table.c.job_id == job_id)

    # FIXME("update the license table")

    count = await database.execute(q)
    return OK(message=f"deleted {job_id} to free {count} product features booked")
