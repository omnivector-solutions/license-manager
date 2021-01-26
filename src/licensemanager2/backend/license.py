"""
License objects and routes
"""
from typing import List, Optional

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
    total: int

    class Config:
        orm_mode = True


class LicenseUseIn(LicenseUseBase):
    """
    Booked/Total counts for a product.feature license category

    For creating a new item.
    """


class LicenseUse(LicenseUseBase):
    """
    Booked/Available/Total counts for a product.feature license category

    Returned by GET queries, including `available` for convenience
    """

    available: Optional[int]

    @validator("available", always=True)
    def validate_available(cls, value, values):
        """
        Set available as a function of the other fields
        """
        return values["total"] - values["booked"]


@router_license.get("/all", response_model=List[LicenseUse])
async def licenses_all():
    """
    All license counts we are tracking
    """
    query = license_table.select()
    return await database.fetch_all(query)


@router_license.get("/{product}", response_model=List[LicenseUse])
async def licenses_product(product: str):
    """
    Booked counts of all licenses, 1 product
    """
    query = license_table.select().where(
        license_table.c.product_feature.like(f"{product}.%")
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


@router_license.patch("/reconcile", response_model=List[LicenseUse])
async def reconcile(reconcile: List[LicenseUseIn]):
    """
    Set counts for models
    """
    reconcile_dict = {i.product_feature: i.dict() for i in reconcile}

    q_updating = (
        select([license_table.c.product_feature])
        .column(license_table.c.product_feature)
        .where(license_table.c.product_feature.in_(list(reconcile_dict.keys())))
    )
    updating = [r[0] for r in await database.fetch_all(q_updating)]
    updates = [reconcile_dict[i] for i in updating]
    for k in updating:
        q_update = (
            update(license_table)
            .where(license_table.c.product_feature == k)
            .values(**reconcile_dict[k])
        )
        # FIXME this sucks, we're blocking once for each update, make asyncer
        await database.execute(q_update)

    inserts = [item for item in reconcile_dict.values() if item not in updates]
    await database.execute_many(query=license_table.insert(), values=inserts)

    fetched = select([license_table]).where(
        license_table.c.product_feature.in_(list(reconcile_dict.keys()))
    )
    ret = await database.fetch_all(fetched)

    return ret


#   /booking PUT
#   /booking DELETE
#   /reconcile PUT
