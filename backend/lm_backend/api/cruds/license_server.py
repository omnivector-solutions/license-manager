from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Configuration, LicenseServer
from lm_backend.database import get_session


class LicenseServerCRUD(GenericCRUD):
    def __init__(self, model, create_schema, update_schema):
        super().__init__(model, create_schema, update_schema)

    async def read_all(self, db_session: AsyncSession):
        async with db_session.begin():
            result = await db_session.execute(select(self.model).order_by(self.model.config_id))
            return result.scalars().all()

    async def read(self, db_session: AsyncSession, id: int):
        async with db_session.begin():
            result = await db_session.execute(select(self.model).where(self.model.id == id))
            license_server = result.scalars().first()
            if not license_server:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License server not found")
            return license_server

    async def delete(self, db_session: AsyncSession, id: int):
        async with db_session.begin():
            result = await db_session.execute(
                select(self.model)
                .options(
                    joinedload(self.model.configurations),
                )
                .where(self.model.id == id)
            )
            license_server = result.scalars().first()
            if not license_server:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License server not found")
            await db_session.delete(license_server)
            await db_session.commit()
            return license_server

    async def filter_by_config_id(self, db_session: AsyncSession, config_id: int):
        async with db_session.begin():
            result = await db_session.execute(
                select(self.model)
                .options(
                    joinedload(self.model.configurations),
                )
                .where(self.model.configurations.any(Configuration.id == config_id))
            )
            return result.scalars().all()
