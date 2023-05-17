from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.schemas import ConfigurationCreateSchema, ConfigurationSchema, ConfigurationUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud = GenericCRUD(Configuration, ConfigurationCreateSchema, ConfigurationUpdateSchema)


@router.post(
    "/",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
async def create_configuration(
    configuration: ConfigurationCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new configuration."""
    return await crud.create(db_session=db_session, obj=configuration)


@router.get(
    "/",
    response_model=List[ConfigurationSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_VIEW))],
)
async def read_all_configurations(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all configurations with the associated license servers and features."""
    return await crud.read_all(
        db_session=db_session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_VIEW))],
)
async def read_configuration(configuration_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a configuration with the associated license severs and features with a given id."""
    return await crud.read(db_session=db_session, id=configuration_id)


@router.put(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
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


@router.delete(
    "/{configuration_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
async def delete_configuration(configuration_id: int, db_session: AsyncSession = Depends(get_session)):
    """
    Delete a configuration from the database.

    This will also delete the features and license servers associated.
    """
    return await crud.delete(db_session=db_session, id=configuration_id)
