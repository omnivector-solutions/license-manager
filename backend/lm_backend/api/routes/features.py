from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.feature import Feature
from lm_backend.api.models.inventory import Inventory
from lm_backend.api.schemas.feature import (
    FeatureCreateSchema,
    FeatureSchema,
    FeatureUpdateSchema,
)
from lm_backend.api.schemas.inventory import (
    InventoryCreateSchema,
    InventoryUpdateSchema,
)
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_feature = GenericCRUD(Feature, FeatureCreateSchema, FeatureUpdateSchema)
crud_inventory = GenericCRUD(Inventory, InventoryCreateSchema, InventoryUpdateSchema)


@router.post(
    "/",
    response_model=FeatureSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.FEATURE_EDIT))],
)
async def create_feature(
    feature: FeatureCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new feature and its inventory."""
    feature = await crud_feature.create(db_session=db_session, obj=feature)
    inventory = InventoryCreateSchema(feature_id=feature.id, total=0, used=0)
    await crud_inventory.create(db_session=db_session, obj=inventory)
    return await crud_feature.read(db_session=db_session, id=feature.id)


@router.get(
    "/",
    response_model=List[FeatureSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.FEATURE_VIEW))],
)
async def read_all_features(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all features with associated bookings and inventory."""
    return await crud_feature.read_all(
        db_session=db_session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/{feature_id}",
    response_model=FeatureSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.FEATURE_VIEW))],
)
async def read_feature(feature_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a feature with associated bookings and inventory with the given id."""
    return await crud_feature.read(db_session=db_session, id=feature_id)


@router.put(
    "/{feature_id}",
    response_model=FeatureSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.FEATURE_EDIT))],
)
async def update_feature(
    feature_id: int,
    feature_update: FeatureUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a feature in the database."""
    return await crud_feature.update(
        db_session=db_session,
        id=feature_id,
        obj=feature_update,
    )


@router.delete(
    "/{feature_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.FEATURE_EDIT))],
)
async def delete_feature(feature_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Delete a feature from the database.

    This will also delete the inventory.
    """
    return await crud_feature.delete(db_session=db_session, id=feature_id)
