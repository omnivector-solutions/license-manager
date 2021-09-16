"""
Booking objects and routes
"""
from typing import List, Union

from fastapi import APIRouter, HTTPException
from sqlalchemy.sql import delete

from lm_backend.api.license import edit_counts, map_bookings
from lm_backend.api_schemas import Booking, BookingRow, ConfigurationRow, LicenseUse, LicenseUseBooking
from lm_backend.compat import INTEGRITY_CHECK_EXCEPTIONS
from lm_backend.storage import database
from lm_backend.table_schemas import booking_table, config_table, license_table

router = APIRouter()


@router.get("/all", response_model=List[BookingRow])
async def get_bookings_all():
    """
    All license counts we are tracking
    """
    query = booking_table.select()
    fetched = await database.fetch_all(query)
    return [BookingRow.parse_obj(x) for x in fetched]


@router.get("/job/{job_id}", response_model=List[BookingRow])
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


async def get_config_id_for_product_features(product_feature: str) -> Union[int, None]:
    product, _ = product_feature.split(".")
    query = config_table.select().where(config_table.c.product == product)
    fetched = await database.fetch_one(query)
    config_row = ConfigurationRow.parse_obj(fetched)
    return config_row.id


async def _is_booking_available(booking: Booking):
    """For each product_feature in the booking.features, check if the total of in_use_total + new_booked
    is <= the total.
    """
    query = booking_table.select()
    fetched = await database.fetch_all(query)
    all_bookings = [BookingRow.parse_obj(x) for x in fetched]

    query = license_table.select()
    fetched = await database.fetch_all(query)
    product_feature_licenses = [LicenseUse.parse_obj(x) for x in fetched]

    for product_feature in booking.features:
        in_use_total = 0
        total = 0
        for license in product_feature_licenses:
            if product_feature.product_feature == license.product_feature:
                in_use_total = license.used
                total = license.total
        for book in all_bookings:
            if product_feature.product_feature != book.product_feature:
                continue
            in_use_total += book.booked

        insert_quantity = product_feature.booked

        if insert_quantity + in_use_total > total:
            return False
    return True


@database.transaction()
@router.put("/book")
async def create_booking(booking: Booking):
    """
    Put a LicenseUse booking object in the database, reserving some tokens

    If an existing product_feature exists for this, update it by incrementing `booked',
    otherwise create it.

    An error occurs if the new total for `booked` exceeds `total`
    """
    if not await _is_booking_available(booking):
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't book {booking.job_id}, not enough licenses available."),
        )
    # update the booking table
    inserts = []

    for feature in booking.features:
        inserts.append(
            BookingRow(
                job_id=booking.job_id,
                product_feature=feature.product_feature,
                booked=feature.booked,
                config_id=await get_config_id_for_product_features(feature.product_feature),
                lead_host=booking.lead_host,
                user_name=booking.user_name,
            )
        )

    inserts_without_id = []
    for insert in inserts:
        inserts_without_id.append(insert.dict(exclude={"id"}))
    try:
        await database.execute_many(query=booking_table.insert(), values=[i for i in inserts_without_id])
    except INTEGRITY_CHECK_EXCEPTIONS as e:
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't book {booking.job_id}, it is already booked\n{e}"),
        )

    # update the license table
    lubs = []
    for feat in booking.features:
        lubs.append(
            LicenseUseBooking(
                product_feature=feat.product_feature,
                used=feat.booked,
            )
        )
    edited = await edit_counts(booking=await map_bookings(lubs))

    return dict(message=f"inserted {booking.job_id} to book {len(edited)} product features")


@database.transaction()
@router.delete("/book/{job_id}")
async def delete_booking(job_id: str):
    """
    Deduct tokens from a LicenseUse booking in the database

    It is an error to use this method with a product_feature that isn't yet in the
    database.  Use reconcile or booking[PUT] to create the target first.

    An error occurs if the new total for `booked` is < 0
    """
    # check that we're deleting a booking that exists
    rows = await get_bookings_job(job_id)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't find booking {job_id} to delete"),
        )

    # update the booking table
    q = delete(booking_table).where(booking_table.c.job_id == job_id)
    await database.execute(q)

    # update the license table
    lubs = []
    for row in rows:
        lubs.append(
            LicenseUseBooking(
                product_feature=row.product_feature,
                used=-row.booked,
            )
        )
    edited = await edit_counts(booking=await map_bookings(lubs))

    return dict(
        message=f"deleted {job_id} to free {len(edited)} product features booked",
    )
