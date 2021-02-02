"""
License objects and routes
"""
import asyncio
from typing import Dict, List, Optional, Sequence, Tuple

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.sql import select, update

from licensemanager2.backend.storage import database
from licensemanager2.backend.storage.schema import license_table


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


@router_license.get("/all", response_model=List[LicenseUse])
async def licenses_all():
    """
    All license counts we are tracking
    """
    query = license_table.select().order_by(license_table.c.product_feature)
    return await database.fetch_all(query)


@router_license.get("/{product}", response_model=List[LicenseUse])
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


@router_license.get("/{product_feature}", response_model=List[LicenseUse])
async def licenses_product_feature(
    product_feature: str = Query(..., regex=PRODUCT_FEATURE_RX)
):
    """
    Booked counts of a product.feature category
    """
    query = license_table.select().where(
        license_table.c.product_feature == product_feature
    )
    return await database.fetch_all(query)


async def _find_license_updates_and_inserts(
    licenses: Sequence[LicenseUseBase],
) -> Tuple[Dict, Dict]:
    """
    Return a dict of updates and a dict of inserts according to whether
    one of the LicenseUses is in the database, or being created
    """
    license_dict = {i.product_feature: i.dict() for i in licenses}

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
            .values(**license_use)
        )
        ops.append(database.execute(q_update))

    # insert new licenses
    ops.append(
        database.execute_many(
            query=license_table.insert(), values=list(inserts.values())
        )
    )

    # wait for all updates and inserts at once
    await asyncio.gather(*ops)

    # query them back out to return them to the client
    requested_keys = [lu.product_feature for lu in reconcile]
    fetched = select([license_table]).where(
        license_table.c.product_feature.in_(requested_keys)
    )
    ret = await database.fetch_all(fetched)

    return ret


@router_license.put("/booking", response_model=List[LicenseUse])
async def create_booking(booking: List[LicenseUseBooking]):
    return []


@router_license.put("/booking", response_model=List[LicenseUse])
async def delete_booking(booking: List[LicenseUseBooking]):
    return []


#   /reconcile PUT
