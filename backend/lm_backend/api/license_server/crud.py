"""CRUD operations for license servers."""
from typing import List, Optional

from sqlalchemy import delete, update
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from lm_backend.api.license_server.schemas import LicenseServerCreateRequest, LicenseServerResponse
from lm_backend.database.models import LicenseServer


class LicenseServerCRUD:
    def __init__(self, async_session: Session):
        self.async_session = async_session

    async def create(self, license_server: LicenseServerCreateRequest) -> LicenseServerResponse:
        """
        Add a new license server to the database.
        Returns the newly created license server or False if creation fails.
        """
        new_license_server = LicenseServer(**license_server.dict())
        try:
            self.async_session.add(new_license_server)
            await self.async_session.flush()
        except Exception:
            return False
        return LicenseServerResponse.from_orm(new_license_server)

    async def read(self, license_server_id: int) -> Optional[LicenseServerResponse]:
        """
        Read a license server with the given id.
        Returns the license server or None if it does not exist.
        """
        query = await self.async_session.execute(
            select(LicenseServer).filter(LicenseServer.id == license_server_id)
        )
        license_server = query.scalar_one_or_none()

        if license_server is None:
            return None

        return LicenseServerResponse.from_orm(license_server)

    async def read_all(self) -> List[LicenseServerResponse]:
        """
        Read all license servers.
        Returns a list of license servers.
        """
        query = await self.async_session.execute(select(LicenseServer))
        license_servers = query.scalars().all()
        return [LicenseServerResponse.from_orm(license_server) for license_server in license_servers]

    async def update(self, license_server_id: int, host: str, port: int, type: str) -> LicenseServerResponse:
        """
        Update a license server in the database.
        Returns the updated license server.
        """
        query = update(LicenseServer).where(LicenseServer.id == license_server_id)
        if host:
            query = query.values(host=host)
        if port:
            query = query.values(port=port)
        if type:
            query = query.values(type=type)
        query.execution_options(synchronize_session="fetch")
        await self.async_session.execute(query)
        await self.async_session.flush()
        return await self.read(license_server_id)

    async def delete(self, license_server_id: int) -> bool:
        """
        Delete a license server from the database.
        Returns True if the license server was deleted, False otherwise.
        """
        query = delete(LicenseServer).where(LicenseServer.id == license_server_id)
        try:
            await self.async_session.execute(query)
            await self.async_session.flush()
        except Exception:
            return False
        return True
