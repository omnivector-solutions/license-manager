"""Feature CRUD class for SQLAlchemy models."""
from typing import List

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.models.product import Product
from lm_backend.api.schemas.feature import FeatureUpdateByNameSchema


class FeatureCRUD(GenericCRUD):
    """Feature CRUD module to implement feature bulk update and lookup."""

    async def bulk_update(
        self, db_session: AsyncSession, features: List[FeatureUpdateByNameSchema], cluster_client_id: str
    ):
        """
        Update a list of features in the database. Since features with the same name can exist in different
        clusters, the client_id is used to filter the cluster where the feature is located.
        """
        get_features_query = (
            select(Feature)
            .join(Product, Feature.product_id == Product.id)
            .join(Configuration, Feature.config_id == Configuration.id)
            .where(
                tuple_(Product.name, Feature.name, Configuration.cluster_client_id,).in_(
                    [(feature.product_name, feature.feature_name, cluster_client_id) for feature in features]
                )
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
            for feature in features:
                if db_obj.product.name == feature.product_name and db_obj.name == feature.feature_name:
                    db_obj.total = feature.total
                    db_obj.used = feature.used
                    break

        try:
            await db_session.flush()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Feature could not be updated.")

    async def filter_by_product_feature_and_client_id(
        self, db_session: AsyncSession, product_name: str, feature_name: str, client_id: str
    ) -> Feature:
        """
        Filter features using the product name and feature name as a filter.
        Since the name is not unique across clusters, the client_id
        in the token is used to identify the cluster.
        """
        filter_features_query = (
            select(Feature)
            .join(Product, Feature.product_id == Product.id)
            .join(Configuration, Feature.config_id == Configuration.id)
            .where(
                tuple_(
                    Product.name,
                    Feature.name,
                    Configuration.cluster_client_id,
                ).in_([(product_name, feature_name, client_id)])
            )
        )
        try:
            query = await db_session.execute(filter_features_query)
            db_obj = query.scalars().one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Feature could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail="Feature not found.")

        return db_obj
