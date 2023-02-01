"""
Booking objects and routes
"""
from ast import literal_eval
from asyncio import Lock
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.sql import delete, join, select

from lm_backend.api.config import get_config_id_for_product_features
from lm_backend.api.permissions import Permissions
from lm_backend.api_schemas import (
    Booking,
    BookingRow,
    BookingRowDetail,
    ConfigurationItem,
    ConfigurationRow,
    LicenseUse,
)
from lm_backend.compat import INTEGRITY_CHECK_EXCEPTIONS
from lm_backend.exceptions import LicenseManagerFeatureConfigurationIncorrect
from lm_backend.security import guard
from lm_backend.storage import database, search_clause, sort_clause
from lm_backend.table_schemas import (
    booking_searchable_fields,
    booking_sortable_fields,
    booking_table,
    config_table,
    license_table,
)

router = APIRouter()

# Lock used to prevent concurrent updates to the booking table
lock = Lock()


@router.get(
    "/all",
    response_model=List[BookingRow],
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_VIEW))],
)
async def get_bookings_all(
    cluster_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
):
    """
    All license counts we are tracking, with the possibility to filter by cluster_name.

    Note that search and sort are not applied if the cluster_name parameter is supplied.
    """
    query = booking_table.select()
    if cluster_name:
        query = query.where(booking_table.c.cluster_name == cluster_name)
    else:
        if search is not None:
            query = query.where(search_clause(search, booking_searchable_fields))
        if sort_field is not None:
            query = query.order_by(sort_clause(sort_field, booking_sortable_fields, sort_ascending))
    fetched = await database.fetch_all(query)
    return [BookingRow.parse_obj(x) for x in fetched]


@router.get(
    "/{booking_id}",
    response_model=BookingRowDetail,
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_VIEW))],
)
async def get_booking(booking_id: int):
    """
    Get details of a single booking by its id.

    Includes the config_name in the returned object.
    """
    query = (
        select([config_table.c.name.label("config_name"), *booking_table.c])
        .select_from(
            join(
                config_table,
                booking_table,
                booking_table.c.config_id == config_table.c.id,
            )
        )
        .where(booking_table.c.id == booking_id)
        .order_by(booking_table.c.product_feature)
    )
    fetched = await database.fetch_one(query)
    return BookingRowDetail.parse_obj(fetched)


@router.get(
    "/job/{job_id}",
    response_model=List[BookingRow],
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_VIEW))],
)
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


async def _get_limit_for_booking_feature(product_feature: str) -> int:
    """
    Get the maximum amount of licenses that can be booked.
    If the limit is the same as the total amount of licenses, all licenses can be booked.

    Possible feature formats:
    -> Old feature format (for retroactive compatibility): limit = total
    features = {"feature1": 123}
    -> New feature format (limit not specified): limit = total
    features = {"feature1": {"total": 123}}
    -> New feature format (limit specified): limit != total
    features = {"feature1": {"total": 123, "limit": 120}}
    """
    product, feature = product_feature.split(".")

    # Use product name to fetch config item from database
    query = config_table.select().where(config_table.c.product == product)
    fetched = await database.fetch_one(query)
    config_row = ConfigurationRow.parse_obj(fetched)
    config_item = ConfigurationItem(
        **config_row.dict(exclude={"features"}), features=literal_eval(config_row.features)
    )

    # Use feature name to get total and limit from feature data in the config item
    try:
        # Get total from new feature format
        total = config_item.features[feature].get("total")
        if not total:
            raise LicenseManagerFeatureConfigurationIncorrect(
                f"The configuration for {feature} is incorrect. Please include the total amount of licenses."
            )
    except AttributeError:
        # Fallback to get the total from the old feature format
        total = config_item.features[feature]

    try:
        # Get limit from new feature format. If not specified, use the total as the limit
        limit = config_item.features[feature].get("limit", total)
    except AttributeError:
        # Fallback to use the total as the limit for the old feature format
        limit = total
    return limit


async def _is_booking_available(booking: Booking) -> bool:
    """
    Check if the total needed for the booking + in_use_total is lower than the limit for the feature.
    If it's not, then there are no more bookings available.
    The in_use_total is calculated accounting for all bookings.
    """
    query = booking_table.select()
    fetched = await database.fetch_all(query)
    all_bookings = [BookingRow.parse_obj(x) for x in fetched]

    query = license_table.select()
    fetched = await database.fetch_all(query)
    all_licenses = [LicenseUse.parse_obj(x) for x in fetched]

    for feature in booking.features:
        in_use_total = 0
        limit = 0
        for license in all_licenses:
            if feature.product_feature == license.product_feature:
                in_use_total = license.used
                limit = await _get_limit_for_booking_feature(license.product_feature)
                break
        for book in all_bookings:
            if feature.product_feature == book.product_feature:
                in_use_total += book.booked

        insert_quantity = feature.booked

        if insert_quantity + in_use_total > limit:
            return False
    return True


@database.transaction()
@router.put(
    "/book",
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_EDIT))],
)
async def create_booking(booking: Booking):
    """
    Put a LicenseUse booking object in the database, reserving some tokens

    If an existing product_feature exists for this, update it by incrementing `booked',
    otherwise create it.

    An error occurs if the new total for `booked` exceeds `total`
    """
    async with lock:
        if not await _is_booking_available(booking):
            raise HTTPException(
                status_code=400,
                detail=f"Couldn't book {booking.job_id}, not enough licenses available.",
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
                    cluster_name=booking.cluster_name,
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
                detail=f"Couldn't book {booking.job_id}, it is already booked\n{e}",
            )

        return dict(message=f"inserted {booking.job_id}")


@database.transaction()
@router.delete(
    "/book/{job_id}",
    dependencies=[Depends(guard.lockdown(Permissions.BOOKING_EDIT))],
)
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

    return dict(
        message=f"deleted {job_id}",
    )
