"""Feature CRUD class for SQLAlchemy models."""
from typing import List, Optional, Sequence, Union

from fastapi import HTTPException
from loguru import logger
from sqlalchemy import Column, func, select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.booking import Booking
from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.product import Product
from lm_api.api.schemas.feature import FeatureSchema, FeatureUpdateByNameSchema
from lm_api.database import search_clause, sort_clause


class FeatureCRUD(GenericCRUD):
    """Feature CRUD module to implement feature bulk update and lookup."""

    async def read(
        self, db_session: AsyncSession, id: Union[Column[int], int], force_refresh: bool = False
    ) -> Optional[Feature]:
        """
        Read a Feature object from the database with the given id.
        Returns the object or raise an exception if it does not exist.
        """
        stmt = (
            select(
                *(Feature.__table__.c),
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.coalesce(func.sum(Booking.quantity), 0).label("booked_total"),
            )
            .join(Product, Feature.product_id == Product.id)
            .join(Booking, Feature.id == Booking.feature_id, isouter=True)
            .where(Feature.id == id)
            .group_by(Feature.id, Product.id)
        )

        try:
            query = await db_session.execute(stmt)
            db_obj = query.first()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be read.")

        if db_obj is None:
            raise HTTPException(status_code=404, detail=f"{self.model.__name__} not found.")

        return FeatureSchema.from_flat_dict(db_obj._asdict())

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
                tuple_(
                    Product.name,
                    Feature.name,
                    Configuration.cluster_client_id,
                ).in_(
                    [(feature.product_name, feature.feature_name, cluster_client_id) for feature in features]
                )
            )
        )

        try:
            result = await db_session.execute(get_features_query)
            db_objs: Sequence[Feature] = result.scalars().all()
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

    async def read_all(
        self,
        db_session: AsyncSession,
        search: Optional[str] = None,
        sort_field: Optional[str] = None,
        sort_ascending: bool = True,
    ) -> List[FeatureSchema]:
        """
        Read all objects.
        Returns a list of objects.
        """
        try:
            stmt = (
                select(
                    *(Feature.__table__.c),
                    Product.id.label("product_id"),
                    Product.name.label("product_name"),
                    func.coalesce(func.sum(Booking.quantity), 0).label("booked_total"),
                )
                .join(Product, Feature.product_id == Product.id)
                .join(Booking, Feature.id == Booking.feature_id, isouter=True)
            )
            if search is not None:
                stmt = stmt.where(search_clause(search, self.model.searchable_fields))
            stmt = stmt.group_by(Feature.id, Product.id)
            if sort_field is not None:
                stmt = stmt.order_by(sort_clause(sort_field, self.model.sortable_fields, sort_ascending))
            query = await db_session.execute(stmt)
            return [FeatureSchema.from_flat_dict(r._asdict()) for r in query.all()]
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__}s could not be read.")
