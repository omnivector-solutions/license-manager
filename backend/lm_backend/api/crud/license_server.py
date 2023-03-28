"""CRUD operations for license servers."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.license_server import (
    LicenseServerCreateSchema,
    LicenseServerSchema,
    LicenseServerUpdateSchema,
)
from lm_backend.models.license_server import LicenseServer


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
            async with db_session.begin():
                db_session.add(new_license_server)
            await db_session.commit()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"License server could not be created: {e}")
        return LicenseServerSchema.from_orm(new_license_server)

    async def read(self, db_session: AsyncSession, license_server_id: int) -> Optional[LicenseServerSchema]:
        """
        Read a license server with the given id.
        Returns the license server or None if it does not exist.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(
                    select(LicenseServer).filter(LicenseServer.id == license_server_id)
                )
                db_license_server = query.scalars().one_or_none()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"License server could not be read: {e}")

        if db_license_server is None:
            raise HTTPException(status_code=404, detail="License server not found")

        return LicenseServerSchema.from_orm(db_license_server)

    async def read_all(self, db_session: AsyncSession) -> List[LicenseServerSchema]:
        """
        Read all license servers.
        Returns a list of license servers.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(select(LicenseServer))
                db_license_servers = query.scalars().all()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"License servers could not be read: {e}")
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
        async with db_session.begin():
            try:
                query = await db_session.execute(
                    select(LicenseServer).filter(LicenseServer.id == license_server_id)
                )
                db_license_server = query.scalar_one_or_none()

                if db_license_server is None:
                    raise HTTPException(status_code=404, detail="License server not found")

                for field, value in license_server_update:
                    if value is not None:
                        setattr(db_license_server, field, value)
                await db_session.flush()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"License server could not be updated: {e}")
        return LicenseServerSchema.from_orm(db_license_server)

    async def delete(self, db_session: AsyncSession, license_server_id: int) -> bool:
        """
        Delete a license server from the database.
        """
        async with db_session.begin():
            try:
                query = await db_session.execute(
                    select(LicenseServer).filter(LicenseServer.id == license_server_id)
                )
                db_license_server = query.scalar_one_or_none()
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"License server could not be deleted: {e}")

            if db_license_server is None:
                raise HTTPException(status_code=404, detail="License server not found")

            try:
                await db_session.delete(db_license_server)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"License server could not be deleted: {e}")
        await db_session.flush()
