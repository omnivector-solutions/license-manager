from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Feature
from lm_backend.api.schemas import (
    FeatureCreateSchema,
    FeatureSchema,
    FeatureUpdateSchema,
    InventoryCreateSchema,
    InventoryUpdateSchema,
)
from lm_backend.database import get_session

router = APIRouter()


crud_feature = GenericCRUD(Feature, FeatureCreateSchema, FeatureUpdateSchema)


@router.post(
    "/",
    response_model=FeatureSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_feature(
    feature: FeatureCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new feature."""
    return await crud_feature.create(db_session=db_session, obj=feature)


@router.get("/", response_model=List[FeatureSchema], status_code=status.HTTP_200_OK)
async def read_all_features(db_session: AsyncSession = Depends(get_session)):
    """Return all features with associated bookings and inventory."""
    return await crud_feature.read_all(db_session=db_session)


@router.get("/{feature_id}", response_model=FeatureSchema, status_code=status.HTTP_200_OK)
async def read_feature(feature_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a feature with associated bookings and inventory with the given id."""
    return await crud_feature.read(db_session=db_session, id=feature_id)


@router.put("/{feature_id}", response_model=FeatureSchema, status_code=status.HTTP_200_OK)
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


@router.delete("/{feature_id}", status_code=status.HTTP_200_OK)
async def delete_feature(feature_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a feature from the database."""
    await crud_feature.delete(db_session=db_session, id=feature_id)
    return {"message": "Feature deleted successfully"}


@router.get("/cluster/{cluster_id}", response_model=List[FeatureSchema], status_code=status.HTTP_200_OK)
async def read_features_in_cluster(cluster_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return all features from a cluster."""
    return await crud_feature.read_by_cluster(db_session=db_session, cluster_id=cluster_id)


@router.post("{feature_id}/inventory", status_code=status.HTTP_200_OK)
async def add_inventory_to_feature(
    feature_id: int,
    inventory: InventoryCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Add inventory to a feature."""
    return await crud_feature.add_inventory(db_session=db_session, feature_id=feature_id, inventory=inventory)


@router.put("{feature_id}/inventory", status_code=status.HTTP_200_OK)
async def update_inventory_in_feature(
    feature_id: int,
    inventory: InventoryUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update inventory in a feature."""
    return await crud_feature.update_inventory(
        db_session=db_session, feature_id=feature_id, inventory=inventory
    )