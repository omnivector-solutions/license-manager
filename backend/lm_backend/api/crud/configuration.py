"""CRUD operations for configurations."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.configuration import (
    ConfigurationCreateSchema,
    ConfigurationSchema,
    ConfigurationUpdateSchema,
)
from lm_backend.models.configuration import Configuration


class ConfigurationCRUD:
    """
    CRUD operations for configurations.
    """

    async def create(
        self, db_session: AsyncSession, configuration: ConfigurationCreateSchema
    ) -> ConfigurationSchema:
        """
        Add a new configuration to the database.
        Returns the newly created configuration.
        """
        new_configuration = Configuration(**configuration.dict())
        try:
            await db_session.add(new_configuration)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="Configuration could not be created")
        return ConfigurationSchema.from_orm(new_configuration)

    async def read(self, db_session: AsyncSession, configuration_id: int) -> Optional[ConfigurationSchema]:
        """
        Read a configuration with the given id.
        Returns the configuration or None if it does not exist.
        """
        query = await db_session.execute(select(Configuration).filter(Configuration.id == configuration_id))
        db_configuration = query.scalars().one_or_none()

        if db_configuration is None:
            raise HTTPException(status_code=404, detail="Configuration not found")

        return ConfigurationSchema.from_orm(db_configuration.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[ConfigurationSchema]:
        """
        Read all configurations.
        Returns a list of configurations.
        """
        query = await db_session.execute(select(Configuration))
        db_configurations = query.scalars().all()
        return [ConfigurationSchema.from_orm(db_configuration) for db_configuration in db_configurations]

    async def update(
        self, db_session: AsyncSession, configuration_id: int, configuration_update: ConfigurationUpdateSchema
    ) -> Optional[ConfigurationSchema]:
        """
        Update a configuration in the database.
        Returns the updated configuration.
        """
        query = await db_session.execute(select(Configuration).filter(Configuration.id == configuration_id))
        db_configuration = query.scalar_one_or_none()

        if db_configuration is None:
            raise HTTPException(status_code=404, detail="Configuration not found")

        for field, value in configuration_update:
            setattr(db_configuration, field, value)

        await db_session.commit()
        await db_session.refresh(db_configuration)
        return ConfigurationSchema.from_orm(db_configuration)

    async def delete(self, db_session: AsyncSession, configuration_id: int) -> bool:
        """
        Delete a configuration from the database.
        """
        query = await db_session.execute(select(Configuration).filter(Configuration.id == configuration_id))
        db_configuration = query.scalars().one_or_none()

        if db_configuration is None:
            raise HTTPException(status_code=404, detail="Configuration not found")
        try:
            db_session.delete(db_configuration)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="Configuration could not be deleted")
