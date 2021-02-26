"""
License objects and routes
"""
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.sql import delete

from licensemanager2.backend.schema import booking_table
from licensemanager2.backend.storage import database
from licensemanager2.common_api import OK
from licensemanager2.compat import INTEGRITY_CHECK_EXCEPTIONS
from licensemanager2.backend import license


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
async def get_bookings_all():
    """
    All license counts we are tracking
    """
    query = booking_table.select().order_by(
        booking_table.c.job_id, booking_table.c.product_feature
    )
    fetched = await database.fetch_all(query)
    return [BookingRow.parse_obj(x) for x in fetched]


@router_booking.get("/job/{job_id}", response_model=List[BookingRow])
async def get_bookings_job(job_id: str):
    """
    All bookings of a particular job
    """
    query = (
        booking_table.select()
        .where(booking_table.c.job_id == job_id)
        .order_by(booking_table.c.product_feature)
    )
    fetched = await database.fetch_all(query)
    return [BookingRow.parse_obj(x) for x in fetched]


@database.transaction()
@router_booking.put("/book", response_model=OK)
async def create_booking(booking: Booking):
    """
    Put a LicenseUse booking object in the database, reserving some tokens

    If an existing product_feature exists for this, update it by incrementing `booked',
    otherwise create it.

    An error occurs if the new total for `booked` exceeds `total`
    """
    # update the booking table
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

    # update the license table
    lubs = []
    for feat in booking.features:
        lubs.append(
            license.LicenseUseBooking(
                product_feature=feat.product_feature,
                booked=feat.booked,
            )
        )
    edited = await license.edit_counts(booking=await license.map_bookings(lubs))

    return OK(message=f"inserted {booking.job_id} to book {len(edited)} product features")


@database.transaction()
@router_booking.delete("/book/{job_id}", response_model=OK)
async def delete_booking(job_id: str):
    """
    Deduct tokens from a LicenseUse booking in the database

    It is an error to use this method with a product_feature that isn't yet in the database.
    Use reconcile or booking[PUT] to create the target first.

    An error occurs if the new total for `booked` is < 0
    """
    # check that we're deleting a booking that exists
    rows = await get_bookings_job(job_id)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Couldn't find booking {job_id} to delete"
            ),
        )

    # update the booking table
    q = delete(booking_table).where(booking_table.c.job_id == job_id)
    await database.execute(q)

    # update the license table
    lubs = []
    for row in rows:
        lubs.append(
            license.LicenseUseBooking(
                product_feature=row["product_feature"],
                booked=-row["booked"],
            )
        )
    edited = await license.edit_counts(booking=await license.map_bookings(lubs))

    return OK(message=f"deleted {job_id} to free {len(edited)} product features booked")
