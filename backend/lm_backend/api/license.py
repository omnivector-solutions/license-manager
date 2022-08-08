import asyncio
from typing import Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.sql import join, select, update

from lm_backend.api.permissions import Permissions
from lm_backend.api_schemas import (
    BookingRow,
    LicenseUse,
    LicenseUseBase,
    LicenseUseReconcile,
    LicenseUseReconcileRequest,
    LicenseUseWithBooking,
)
from lm_backend.helpers import LicenseUseSortFieldChecker, LicenseUseWithBookingSortFieldChecker
from lm_backend.security import guard
from lm_backend.storage import database, search_clause
from lm_backend.table_schemas import booking_table, license_searchable_fields, license_table

PRODUCT_FEATURE_RX = r"^.+?\..+$"
router = APIRouter()


@router.get(
    "/all",
    response_model=List[LicenseUse],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_VIEW))],
)
async def licenses_all(
    search: Optional[str] = Query(None),
    sort_field: str = Depends(LicenseUseSortFieldChecker()),
    sort_ascending: bool = Query(True),
):
    """
    All license counts we are tracking
    """
    query = license_table.select().order_by(license_table.c.product_feature)

    if search is not None:
        query = query.where(search_clause(search, license_searchable_fields))

    fetched = await database.fetch_all(query)
    licenses = [LicenseUse.parse_obj(x) for x in fetched]

    if sort_field is not None:
        licenses = sorted(
            licenses, key=lambda license: getattr(license, sort_field), reverse=not sort_ascending
        )

    return licenses


@router.get(
    "/complete/all",
    response_model=List[LicenseUseWithBooking],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_VIEW))],
)
async def licenses_all_with_booking(
    search: Optional[str] = Query(None),
    sort_field: str = Depends(LicenseUseWithBookingSortFieldChecker()),
    sort_ascending: bool = Query(True),
):
    """
    All license counts we are tracking with booked tokens included.
    """
    query = (
        select([*license_table.c, func.sum(func.coalesce(booking_table.c.booked, 0)).label("booked")])
        .select_from(
            join(
                license_table,
                booking_table,
                license_table.c.product_feature == booking_table.c.product_feature,
                isouter=True,
            )
        )
        .group_by(
            license_table.c.id,
            license_table.c.product_feature,
        )
        .order_by(license_table.c.product_feature)
    )
    if search is not None:
        query = query.where(search_clause(search, license_searchable_fields))

    fetched = await database.fetch_all(query)
    licenses = [LicenseUseWithBooking.parse_obj(x) for x in fetched]

    if sort_field is not None:
        licenses = sorted(
            licenses, key=lambda license: getattr(license, sort_field), reverse=not sort_ascending
        )

    return licenses


@router.get(
    "/cluster_update",
    response_model=List[Dict],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_VIEW))],
)
async def licenses_and_bookings_to_update():
    """
    Get the actual value to update the cluster for each license.
    """
    query = license_table.select()
    fetched = await database.fetch_all(query)
    all_licenses = [LicenseUse.parse_obj(x) for x in fetched]

    query = booking_table.select()
    fetched = await database.fetch_all(query)
    all_bookings = [BookingRow.parse_obj(x) for x in fetched]

    licenses_to_update_data: List = []
    for license in all_licenses:
        licenses_to_update_data.append(
            {
                "product_feature": license.product_feature,
                "bookings_sum": sum(
                    [
                        booking.booked
                        for booking in all_bookings
                        if booking.product_feature == license.product_feature
                    ]
                ),
                "license_total": license.total,
                "license_used": license.used,
            }
        )
    return licenses_to_update_data


@router.get(
    "/use/{product}",
    response_model=List[LicenseUse],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_VIEW))],
)
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


@router.get(
    "/use/{product}/{feature}",
    response_model=List[LicenseUse],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_VIEW))],
)
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

    q_updating = select([license_table.c.product_feature]).where(
        license_table.c.product_feature.in_(list(license_dict.keys()))
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
@router.patch(
    "/reconcile",
    response_model=List[LicenseUse],
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_EDIT))],
)
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
