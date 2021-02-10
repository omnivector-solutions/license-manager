"""
License objects and routes
"""
import asyncio
from typing import Any, Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.sql import select, update

from licensemanager2.backend.schema import license_table
from licensemanager2.backend.settings import SETTINGS
from licensemanager2.backend.storage import database
from licensemanager2.common_response import OK
from licensemanager2.compat import INTEGRITY_CHECK_EXCEPTIONS


PRODUCT_FEATURE_RX = r"^.+?\..+$"


router_license = APIRouter()


class LicenseUseBase(BaseModel):
    """
    Booked/Total counts for a product.feature license category
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    booked: int

    class Config:
        orm_mode = True


class LicenseUseReconcile(LicenseUseBase):
    """
    A reconcile [PATCH] Booked/Total counts for a product.feature license category

    For creating items through the reconcile mechanism
    """

    total: int


class LicenseUse(LicenseUseBase):
    """
    Booked/Available/Total counts for a product.feature license category

    Returned by GET queries, including `available` for convenience
    """

    total: int

    available: Optional[int]

    @validator("available", always=True)
    def validate_available(cls, value, values):
        """
        Set available as a function of the other fields
        """
        return values["total"] - values["booked"]


class LicenseUseBooking(LicenseUseBase):
    """
    A booking [PUT] object, specifying how many tokens are needed and no total
    """


@router_license.get("/use/all", response_model=List[LicenseUse])
async def licenses_all():
    """
    All license counts we are tracking
    """
    query = license_table.select().order_by(license_table.c.product_feature)
    return await database.fetch_all(query)


@router_license.get("/use/{product}", response_model=List[LicenseUse])
async def licenses_product(product: str):
    """
    Booked counts of all licenses, 1 product
    """
    query = (
        license_table.select()
        .where(license_table.c.product_feature.like(f"{product}.%"))
        .order_by(license_table.c.product_feature)
    )
    return await database.fetch_all(query)


@router_license.get("/use/{product}/{feature}", response_model=List[LicenseUse])
async def licenses_product_feature(product: str, feature: str):
    """
    Booked counts of a product.feature category
    """
    query = license_table.select().where(
        license_table.c.product_feature == f"{product}.{feature}"
    )
    return await database.fetch_all(query)


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


@database.transaction()
@router_license.patch("/reconcile", response_model=List[LicenseUse])
async def reconcile(reconcile: List[LicenseUseReconcile]):
    """
    Set counts for models
    """
    updates, inserts = await _find_license_updates_and_inserts(reconcile)

    ops = []
    # update existing licenses
    for pf, license_use in updates.items():
        q_update = (
            update(license_table)
            .where(license_table.c.product_feature == pf)
            .values(**license_use.dict())
        )
        ops.append(database.execute(q_update))

    # insert new licenses
    ops.append(
        database.execute_many(
            query=license_table.insert(), values=[i.dict() for i in inserts.values()]
        )
    )

    # wait for all updates and inserts at once
    await asyncio.gather(*ops)

    # query them back out to return them to the client
    requested_keys = [lu.product_feature for lu in reconcile]
    return await _get_these_licenses(requested_keys)


def debug():
    """
    Enforce debug mode

    FIXME - move this somewhere like common_dependencies
    """
    if not SETTINGS.DEBUG:
        raise HTTPException(status_code=403)


@database.transaction()
@router_license.put("/reconcile", response_model=OK)
async def reconcile_reset(
    debug: Any = Depends(debug), x_reconcile_reset: Any = Header(...)
):
    """
    Reset all license data (only permitted in DEBUG mode)

    Set the header `X-Reconcile-Reset:` to anything you want.
    """
    await database.execute(license_table.delete())
    return OK()


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
                "Use /reconcile first to set the totals, or remove them from the request."
            ),
        )
    return updates


@database.transaction()
@router_license.put("/booking", response_model=List[LicenseUse])
async def create_booking(booking=Depends(map_bookings)):
    """
    Put a LicenseUse booking object in the database, reserving some tokens

    If an existing product_feature exists for this, update it by incrementing `booked',
    otherwise create it.

    An error occurs if the new total for `booked` exceeds `total`
    """
    ops = []
    for pf, license_use in booking.items():
        q_update = (
            update(license_table)
            .where(license_table.c.product_feature == pf)
            .values(booked=license_table.c.booked + license_use.booked)
        )
        ops.append(database.execute(q_update))

    # wait for all updates at once
    try:
        await asyncio.gather(*ops)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Couldn't add one of these bookings, check that the new booked count will be <= total"
            ),
        )
    return await _get_these_licenses(list(booking.keys()))


@database.transaction()
@router_license.delete("/booking", response_model=List[LicenseUse])
async def delete_booking(booking=Depends(map_bookings)):
    """
    Deduct tokens from a LicenseUse booking in the database

    It is an error to use this method with a product_feature that isn't yet in the database.
    Use reconcile or booking[PUT] to create the target first.

    An error occurs if the new total for `booked` is < 0
    """
    ops = []
    for pf, license_use in booking.items():
        q_update = (
            update(license_table)
            .where(license_table.c.product_feature == pf)
            .values(booked=license_table.c.booked - license_use.booked)
        )
        ops.append(database.execute(q_update))

    # wait for all updates at once
    try:
        await asyncio.gather(*ops)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Couldn't subtract one of these bookings, check that the new booked count will be >= 0"
            ),
        )

    return await _get_these_licenses(list(booking.keys()))
