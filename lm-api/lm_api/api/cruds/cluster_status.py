"""Cluster CRUD class for SQLAlchemy models."""
from fastapi import HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from typing import Optional
from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.cluster_status import ClusterStatus
from lm_api.api.schemas.cluster_status import ClusterStatusSchema


class ClusterStatusCRUD(GenericCRUD):
    """Cluster CRUD module to implement PUT endpoint for cluster status update."""

    async def upsert(
        self,
        db_session: AsyncSession,
        payload: ClusterStatusSchema,
    ) -> Optional[ClusterStatus]:
        """Creates a new cluster status update or updates the existing one."""
        try:
            stmt = select(ClusterStatus).filter(ClusterStatus.cluster_client_id == payload.cluster_client_id)
            query = await db_session.execute(stmt)
            db_obj = query.scalar_one_or_none()
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be read.")

        if db_obj is None:
            create_obj = self.model(**payload.model_dump())
            try:
                db_session.add(create_obj)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be created.")

            await db_session.flush()
            await db_session.refresh(create_obj)
            return db_obj
        else:
            for field, value in payload:
                if hasattr(db_obj, field) and value is not None:
                    setattr(db_obj, field, value)

            try:
                await db_session.flush()
                await db_session.refresh(db_obj)
            except Exception as e:
                logger.error(e)
                raise HTTPException(status_code=400, detail=f"{self.model.__name__} could not be updated.")

            return db_obj
