import asyncio
from typing import Dict, List, Sequence, Tuple

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.sql import select, update

from lm_backend.api_schemas import (
    BookingRow,
    LicenseUse,
    LicenseUseBase,
    LicenseUseBooking,
    LicenseUseReconcile,
    LicenseUseReconcileRequest,
)
from lm_backend.compat import INTEGRITY_CHECK_EXCEPTIONS
from lm_backend.storage import database
from lm_backend.table_schemas import booking_table, license_table

PRODUCT_FEATURE_RX = r"^.+?\..+$"
router = APIRouter()


@router.get("/all", response_model=List[LicenseUse])
async def licenses_all():
    """
    All license counts we are tracking
    """
    query = license_table.select().order_by(license_table.c.product_feature)
    fetched = await database.fetch_all(query)
    return [LicenseUse.parse_obj(x) for x in fetched]


@router.get("/use/{product}", response_model=List[LicenseUse])
async def licenses_product(product: str):
    """
    Used counts of all licenses, 1 product
    """
    query = (
        license_table.select()
        .where(license_table.c.product_feature.like(f"{product}.%"))
        .order_by(license_table.c.product_feature)
    )
    fetched = await database.fetch_all(query)
    return [LicenseUse.parse_obj(x) for x in fetched]


@router.get("/use/{product}/{feature}", response_model=List[LicenseUse])
async def licenses_product_feature(product: str, feature: str):
    """
    Used counts of a product.feature category
    """
    query = license_table.select().where(license_table.c.product_feature == f"{product}.{feature}")
    fetched = await database.fetch_all(query)
    return [LicenseUse.parse_obj(x) for x in fetched]


async def _find_license_updates_and_inserts(
    licenses: Sequence[LicenseUseBase],
) -> Tuple[Dict, Dict]:
    """
    Return a dict of updates and a dict of inserts according to whether
    one of the LicenseUses is in the database, or being created
    """
    license_dict = {i.product_feature: i for i in licenses}

    q_updating = (
        select([license_table.c.product_feature])
        .column(license_table.c.product_feature)
        .where(license_table.c.product_feature.in_(list(license_dict.keys())))
    )
    updating = [r[0] for r in await database.fetch_all(q_updating)]
    not_updating = list(set(license_dict.keys()) - set(updating))

    updates = {pf: license_dict[pf] for pf in updating}
    inserts = {pf: license_dict[pf] for pf in not_updating}

    return updates, inserts


async def _get_these_licenses(product_features: Sequence[str]) -> List[LicenseUse]:
    """
    Fetch the specific list of licenses matching the argument
    """
    fetch_query = (
        select([license_table])
        .where(license_table.c.product_feature.in_(product_features))
        .order_by(license_table.c.product_feature)
    )
    fetched = await database.fetch_all(fetch_query)
    return [LicenseUse.parse_obj(f) for f in fetched]


async def _delete_if_in_use_booking(license: LicenseUseReconcileRequest):
    """
    Check the database for the license, if it is booked, then delete it.
    """
    queries = []
    for used_license in license.used_licenses:
        query = (
            booking_table.select()
            .where(booking_table.c.lead_host == used_license["lead_host"])
            .where(booking_table.c.user_name == used_license["user_name"])
            .where(booking_table.c.booked == used_license["booked"])
            .where(booking_table.c.product_feature == license.product_feature)
        )
        queries.append(database.fetch_one(query))
    fetched = await asyncio.gather(*queries)
    bookings = [BookingRow.parse_obj(item) for item in fetched if item is not None]
    if not bookings:
        return

    delete_queries = []
    for booking in bookings:
        delete_query = booking_table.delete().where(booking_table.c.id == booking.id)
        delete_queries.append(database.execute(delete_query))
    await asyncio.gather(*delete_queries)


async def _clean_up_in_use_booking(
    reconcile_request: List[LicenseUseReconcileRequest],
) -> List[LicenseUseReconcile]:
    """
    For each license in the reconcile check if the {lead_host}{user_name}{booked} matches something in the
    database, then delete these bookings because they are already in use.
    """
    reconcile = []
    for license in reconcile_request:
        await _delete_if_in_use_booking(license)
        reconcile.append(LicenseUseReconcile(**license.dict(exclude={"used_licenses"})))

    return reconcile


@database.transaction()
@router.patch("/reconcile", response_model=List[LicenseUse])
async def reconcile_changes(reconcile_request: List[LicenseUseReconcileRequest]):
    """
    Set counts for models
    """
    reconcile = await _clean_up_in_use_booking(reconcile_request)
    updates, inserts = await _find_license_updates_and_inserts(reconcile)

    ops = []
    # update existing licenses
    for pf, license_use in updates.items():
        q_update = (
            update(license_table).where(license_table.c.product_feature == pf).values(**license_use.dict())
        )
        ops.append(database.execute(q_update))

    # insert new licenses
    ops.append(
        database.execute_many(query=license_table.insert(), values=[i.dict() for i in inserts.values()])
    )

    # wait for all updates and inserts at once
    await asyncio.gather(*ops)

    # query them back out to return them to the client
    requested_keys = [lu.product_feature for lu in reconcile]
    return await _get_these_licenses(requested_keys)


async def map_bookings(
    booking: List[LicenseUseBooking],
) -> Dict[str, LicenseUseBooking]:
    """
    For bookings, map the object to a dict with the pk as the dictionary key
    This also validates that all the bookings are for licenses that exist.
    """
    updates, inserts = await _find_license_updates_and_inserts(booking)
    if inserts:
        raise HTTPException(
            status_code=400,
            detail=(
                "Some requested licenses don't exist yet. "
                "Use /reconcile first to set the totals, "
                "or remove them from the request."
            ),
        )
    return updates


@database.transaction()
@router.put("/edit-counts", response_model=List[LicenseUse])
async def edit_counts(booking=Depends(map_bookings)):
    """
    Modify a LicenseUse in the database by adding or subtracting t okens.

    If an existing product_feature exists for this, update it by incrementing `used',
    otherwise create it.

    An error occurs if the new amount for `used` exceeds `total` or is <0
    """
    ops = []
    for pf, license_use in booking.items():
        q_update = (
            update(license_table)
            .where(license_table.c.product_feature == pf)
            .values(used=license_table.c.used + license_use.used)
        )
        ops.append(database.execute(q_update))

    # TODO! test decrementing a counter that doesn't exist yet (<0)

    # wait for all updates at once
    try:
        await asyncio.gather(*ops)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=("Couldn't add one of these counts, " "check that the new used count will be <= total"),
        )
    return await _get_these_licenses(list(booking.keys()))
