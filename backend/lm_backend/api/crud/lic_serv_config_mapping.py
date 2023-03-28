"""CRUD operations for license server config mapping."""
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from lm_backend.api.schemas.lic_serv_config_mapping import (
    LicServConfigMappingCreateSchema,
    LicServConfigMappingSchema,
    LicServConfigMappingUpdateSchema,
)
from lm_backend.models.lic_serv_config_mapping import LicServConfigMapping


class LicServConfigMappingCRUD:
    """
    CRUD operations for license server config mapping.
    """

    async def create(
        self, db_session: AsyncSession, lic_serv_config_mapping: LicServConfigMappingCreateSchema
    ) -> LicServConfigMappingSchema:
        """
        Add a new lic_serv_config_mapping to the database.
        Returns the newly created lic_serv_config_mapping.
        """
        new_lic_serv_config_mapping = LicServConfigMapping(**lic_serv_config_mapping.dict())
        try:
            await db_session.add(new_lic_serv_config_mapping)
            await db_session.commit()
        except Exception as e:
            print(e)
            raise HTTPException(status_code=400, detail="LicServConfigMapping could not be created")
        return LicServConfigMappingSchema.from_orm(new_lic_serv_config_mapping)

    async def read(
        self, db_session: AsyncSession, config_id: int, license_server_id: int
    ) -> Optional[LicServConfigMappingSchema]:
        """
        Read a lic_serv_config_mapping with the given id.
        Returns the lic_serv_config_mapping.
        """
        query = await db_session.execute(
            select(LicServConfigMapping).filter(
                LicServConfigMapping.config_id == config_id,
                LicServConfigMapping.license_server_id == license_server_id,
            )
        )
        db_lic_serv_config_mapping = query.scalars().one_or_none()

        if db_lic_serv_config_mapping is None:
            raise HTTPException(status_code=404, detail="LicServConfigMapping not found")

        return LicServConfigMappingSchema.from_orm(db_lic_serv_config_mapping.scalar_one_or_none())

    async def read_all(self, db_session: AsyncSession) -> List[LicServConfigMappingSchema]:
        """
        Read all lic_serv_config_mappings.
        Returns a list of lic_serv_config_mappings.
        """
        query = await db_session.execute(select(LicServConfigMapping))
        db_lic_serv_config_mappings = query.scalars().all()
        return [
            LicServConfigMappingSchema.from_orm(db_lic_serv_config_mapping)
            for db_lic_serv_config_mapping in db_lic_serv_config_mappings
        ]

    async def update(
        self,
        db_session: AsyncSession,
        lic_serv_config_mapping_config_id: int,
        lic_serv_config_mapping_license_server_id: int,
        lic_serv_config_mapping_update: LicServConfigMappingUpdateSchema,
    ) -> Optional[LicServConfigMappingSchema]:
        """
        Update a lic_serv_config_mapping in the database.
        Returns the updated lic_serv_config_mapping.
        """
        query = await db_session.execute(
            select(LicServConfigMapping).filter(
                LicServConfigMapping.config_id == lic_serv_config_mapping_config_id,
                LicServConfigMapping.license_server_id == lic_serv_config_mapping_license_server_id,
            )
        )
        db_lic_serv_config_mapping = query.scalar_one_or_none()

        if db_lic_serv_config_mapping is None:
            raise HTTPException(status_code=404, detail="LicServConfigMapping not found")

        for field, value in lic_serv_config_mapping_update:
            setattr(db_lic_serv_config_mapping, field, value)

        await db_session.commit()
        await db_session.refresh(db_lic_serv_config_mapping)
        return LicServConfigMappingSchema.from_orm(db_lic_serv_config_mapping)

    async def delete(
        self,
        db_session: AsyncSession,
        lic_serv_config_mapping_config_id: int,
        lic_serv_config_mapping_license_server_id,
    ):
        """
        Delete a lic_serv_config_mapping from the database.
        """
        query = await db_session.execute(
            select(LicServConfigMapping).filter(
                LicServConfigMapping.config_id == lic_serv_config_mapping_config_id,
                LicServConfigMapping.license_server_id == lic_serv_config_mapping_license_server_id,
            )
        )
        db_lic_serv_config_mapping = query.scalars().one_or_none()

        if db_lic_serv_config_mapping is None:
            raise HTTPException(status_code=404, detail="LicServConfigMapping not found")
        try:
            db_session.delete(db_lic_serv_config_mapping)
            await db_session.flush()
        except Exception:
            raise HTTPException(status_code=400, detail="LicServConfigMapping could not be deleted")
