"""Feature CRUD class for SQLAlchemy models."""
from typing import Dict

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.schemas.feature import FeatureUpdateByNameSchema


class FeatureCRUD(GenericCRUD):
    """Feature CRUD module to implement feature bulk update and lookup."""

    async def bulk_update(
        self, db_session: AsyncSession, features: Dict[str, FeatureUpdateByNameSchema], cluster_client_id: str
    ):
        """
        Update a list of features in the database. Since features with the same name can exist in different
        clusters, the client_id is used to filter the cluster where the feature is located.
        """
        get_features_query = (
            select(Feature)
            .join(Configuration)
            .where(
                tuple_(
                    Feature.name,
                    Configuration.cluster_client_id,
                ).in_([(feature, cluster_client_id) for feature in features])
            )
        )

        try:
            result = await db_session.execute(get_features_query)
            db_objs = result.scalars().all()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Feature could not be read.")

        if len(db_objs) != len(features):
            raise HTTPException(status_code=404, detail="Feature not found.")

        for db_obj in db_objs:
            feature = features[db_obj.name]
            db_obj.total = feature.total
            db_obj.used = feature.used

        try:
            await db_session.flush()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Feature could not be updated.")
