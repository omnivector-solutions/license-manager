from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.license_server import LicenseServer
from lm_backend.api.schemas.license_server import (
    LicenseServerCreateSchema,
    LicenseServerSchema,
    LicenseServerUpdateSchema,
)
from lm_backend.constants import LicenseServerType
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud_license_server = GenericCRUD(LicenseServer, LicenseServerCreateSchema, LicenseServerUpdateSchema)


@router.get(
    "/types/",
    status_code=status.HTTP_200_OK,
    response_model=List[LicenseServerType],
)
async def get_license_server_types(
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_VIEW)),
):
    """Return a list of the available license server types."""
    return list(LicenseServerType)


@router.post(
    "",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_license_server(
    license_server: LicenseServerCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_EDIT)),
):
    """Create a new license server."""
    return await crud_license_server.create(db_session=secure_session.session, obj=license_server)


@router.get(
    "",
    response_model=List[LicenseServerSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_license_servers(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_VIEW)),
):
    """Return all license servers."""
    return await crud_license_server.read_all(
        db_session=secure_session.session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{license_server_id}",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_200_OK,
)
async def read_license_server(
    license_server_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_VIEW)),
):
    """Return a license server with the given id."""
    return await crud_license_server.read(db_session=secure_session.session, id=license_server_id)


@router.put(
    "/{license_server_id}",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_200_OK,
)
async def update_license_server(
    license_server_id: int,
    license_server_update: LicenseServerUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_EDIT)),
):
    """Update a license server in the database."""
    return await crud_license_server.update(
        db_session=secure_session.session,
        id=license_server_id,
        obj=license_server_update,
    )


@router.delete(
    "/{license_server_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_license_server(
    license_server_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.LICENSE_SERVER_EDIT)),
):
    """Delete a license server from the database."""
    return await crud_license_server.delete(db_session=secure_session.session, id=license_server_id)
