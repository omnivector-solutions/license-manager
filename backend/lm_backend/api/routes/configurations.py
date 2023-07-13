from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.schemas.configuration import (
    ConfigurationCreateSchema,
    ConfigurationSchema,
    ConfigurationUpdateSchema,
)
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud = GenericCRUD(Configuration, ConfigurationCreateSchema, ConfigurationUpdateSchema)


@router.post(
    "/",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_configuration(
    configuration: ConfigurationCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """Create a new configuration."""
    return await crud.create(db_session=secure_session.session, obj=configuration)


@router.get(
    "/",
    response_model=List[ConfigurationSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_configurations(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_VIEW)),
):
    """Return all configurations with the associated license servers and features."""
    return await crud.read_all(
        db_session=secure_session.session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
)
async def read_configuration(
    configuration_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_VIEW)),
):
    """Return a configuration with the associated license severs and features with a given id."""
    return await crud.read(db_session=secure_session.session, id=configuration_id)


@router.put(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
)
async def update_configuration(
    configuration_id: int,
    configuration_update: ConfigurationUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """Update a configuration in the database."""
    return await crud.update(
        db_session=secure_session.session,
        id=configuration_id,
        obj=configuration_update,
    )


@router.delete(
    "/{configuration_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_configuration(
    configuration_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """
    Delete a configuration from the database.

    This will also delete the features and license servers associated.
    """
    return await crud.delete(db_session=secure_session.session, id=configuration_id)
