"""CRUD operations for license servers."""
from typing import List, Optional

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.schemas.license_server import (
    LicenseServerCreateSchema,
    LicenseServerUpdateSchema,
    LicenseServerSchema,
)
from lm_backend.models.license_server import LicenseServer

from fastapi import HTTPException


class LicenseServerCRUD:
    """
    CRUD operations for license servers.
    """

    async def create(
        self, db_session: AsyncSession, license_server: LicenseServerCreateSchema
    ) -> LicenseServerSchema:
        """
        Add a new license server to the database.
        Returns the newly created license server.
        """
        new_license_server = LicenseServer(**license_server.dict())
        try:
            await db_session.add(new_license_server)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="License server could not be created")
        return LicenseServerSchema.from_orm(new_license_server)

    async def read(self, db_session: AsyncSession, license_server_id: int) -> Optional[LicenseServerSchema]:
        """
        Read a license server with the given id.
        Returns the license server or None if it does not exist.
        """
        query = await db_session.execute(select(LicenseServer).filter(LicenseServer.id == license_server_id))
        db_license_server = query.scalars().one_or_none()

        if db_license_server is None:
            raise HTTPException(status_code=404, detail="License server not found")

        return LicenseServerSchema.from_orm(db_license_server.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[LicenseServerSchema]:
        """
        Read all license servers.
        Returns a list of license servers.
        """
        query = await db_session.execute(select(LicenseServer))
        db_license_servers = query.scalars().all()
        return [LicenseServerSchema.from_orm(db_license_server) for db_license_server in db_license_servers]

    async def update(
        self,
        db_session: AsyncSession,
        license_server_id: int,
        license_server_update: LicenseServerUpdateSchema,
    ) -> Optional[LicenseServerSchema]:
        """
        Update a license server in the database.
        Returns the updated license server.
        """
        query = await db_session.execute(select(LicenseServer).filter(LicenseServer.id == license_server_id))
        db_license_server = query.scalar_one_or_none()

        if db_license_server is None:
            raise HTTPException(status_code=404, detail="License server not found")

        for field, value in license_server_update:
            setattr(db_license_server, field, value)

        await db_session.commit()
        await db_session.refresh(db_license_server)
        return LicenseServerSchema.from_orm(db_license_server)

    async def delete(self, db_session: AsyncSession, license_server_id: int) -> bool:
        """
        Delete a license server from the database.
        """
        query = await db_session.execute(select(LicenseServer).filter(LicenseServer.id == license_server_id))
        db_license_server = query.scalars().one_or_none()

        if db_license_server is None:
            raise HTTPException(status_code=404, detail="License server not found")
        try:
            db_session.delete(db_license_server)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="License server could not be deleted")
