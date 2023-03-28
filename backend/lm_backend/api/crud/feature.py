"""CRUD operations for features."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.feature import FeatureCreateSchema, FeatureSchema, FeatureUpdateSchema
from lm_backend.models.feature import Feature


class FeatureCRUD:
    """
    CRUD operations for features.
    """

    async def create(self, db_session: AsyncSession, feature: FeatureCreateSchema) -> FeatureSchema:
        """
        Add a new feature to the database.
        Returns the newly created feature.
        """
        new_feature = Feature(**feature.dict())
        try:
            await db_session.add(new_feature)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Feature could not be created")
        return FeatureSchema.from_orm(new_feature)

    async def read(self, db_session: AsyncSession, feature_id: int) -> Optional[FeatureSchema]:
        """
        Read a feature with the given id.
        Returns the feature.
        """
        query = await db_session.execute(select(Feature).filter(Feature.id == feature_id))
        db_feature = query.scalars().one_or_none()

        if db_feature is None:
            raise HTTPException(status_code=404, detail="Feature not found")

        return FeatureSchema.from_orm(db_feature.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[FeatureSchema]:
        """
        Read all features.
        Returns a list of features.
        """
        query = await db_session.execute(select(Feature))
        db_features = query.scalars().all()
        return [FeatureSchema.from_orm(db_feature) for db_feature in db_features]

    async def update(
        self, db_session: AsyncSession, feature_id: int, feature_update: FeatureUpdateSchema
    ) -> Optional[FeatureSchema]:
        """
        Update a feature in the database.
        Returns the updated feature.
        """
        query = await db_session.execute(select(Feature).filter(Feature.id == feature_id))
        db_feature = query.scalar_one_or_none()

        if db_feature is None:
            raise HTTPException(status_code=404, detail="Feature not found")

        for field, value in feature_update:
            setattr(db_feature, field, value)

        await db_session.commit()
        await db_session.refresh(db_feature)
        return FeatureSchema.from_orm(db_feature)

    async def delete(self, db_session: AsyncSession, feature_id: int) -> bool:
        """
        Delete a feature from the database.
        """
        query = await db_session.execute(select(Feature).filter(Feature.id == feature_id))
        db_feature = query.scalars().one_or_none()

        if db_feature is None:
            raise HTTPException(status_code=404, detail="Feature not found")
        try:
            db_session.delete(db_feature)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Feature could not be deleted")
