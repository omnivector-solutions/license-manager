"""Feature CRUD class for SQLAlchemy models."""
from fastapi import HTTPException
from loguru import logger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.feature import Feature
from lm_api.api.models.license_server import LicenseServer
from lm_api.api.schemas.configuration import ConfigurationCompleteUpdateSchema


class ConfigurationCRUD(GenericCRUD):
    """Configuration CRUD module to implement configuration update."""

    async def delete_features(
        self, db_session: AsyncSession, configuration_id: int, payload: ConfigurationCompleteUpdateSchema
    ):
        """
        Delete all features that aren't in the payload.
        """
        features_in_payload = [f.id for f in payload.features if f.id is not None] if payload.features else []
        delete_unused_features_query = (
            delete(Feature)
            .where(~Feature.id.in_(features_in_payload))
            .where(Feature.config_id == configuration_id)
        )

        try:
            await db_session.execute(delete_unused_features_query)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="Feature could not be deleted.")

    async def delete_license_servers(
        self, db_session: AsyncSession, configuration_id: int, payload: ConfigurationCompleteUpdateSchema
    ):
        """
        Delete all license servers that aren't in the payload.
        """
        license_servers_in_payload = (
            [ls.id for ls in payload.license_servers if ls.id is not None] if payload.license_servers else []
        )
        delete_unused_license_servers_query = (
            delete(LicenseServer)
            .where(~LicenseServer.id.in_(license_servers_in_payload))
            .where(LicenseServer.config_id == configuration_id)
        )

        try:
            await db_session.execute(delete_unused_license_servers_query)
        except Exception as e:
            logger.error(e)
            raise HTTPException(status_code=400, detail="License Server could not be deleted.")
