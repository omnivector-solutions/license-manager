from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import Configuration
from lm_backend.api.schemas import ConfigurationCreateSchema, ConfigurationSchema, ConfigurationUpdateSchema
from lm_backend.database import get_session

router = APIRouter()


crud = GenericCRUD(Configuration, ConfigurationCreateSchema, ConfigurationUpdateSchema)


@router.post(
    "/",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_configuration(
    configuration: ConfigurationCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new configuration."""
    return await crud.create(db_session=db_session, obj=configuration)


@router.get("/", response_model=List[ConfigurationSchema], status_code=status.HTTP_200_OK)
async def read_all_configurations(db_session: AsyncSession = Depends(get_session)):
    """Return all configurations with the associated license servers and features."""
    # return await crud.read_all(db_session=db_session, options=selectinload(Configuration.license_servers, selectinload(Configuration.features))


@router.get("/{configuration_id}", response_model=ConfigurationSchema, status_code=status.HTTP_200_OK)
async def read_configuration(configuration_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a configuration with the associated license severs and features with a given id."""
    # return await crud.read(db_session=db_session, id=configuration_id, options=selectinload(Configuration.license_servers, Configuration.features))


@router.put("/{configuration_id}", response_model=ConfigurationSchema, status_code=status.HTTP_200_OK)
async def update_configuration(
    configuration_id: int,
    configuration_update: ConfigurationUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a configuration in the database."""
    return await crud.update(
        db_session=db_session,
        id=configuration_id,
        obj=configuration_update,
    )


@router.delete("/{configuration_id}", status_code=status.HTTP_200_OK)
async def delete_configuration(configuration_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a configuration from the database."""
    await crud.delete(db_session=db_session, id=configuration_id)
    return {"message": "Configuration deleted successfully"}
