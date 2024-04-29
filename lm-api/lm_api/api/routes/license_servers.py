from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query, status

from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.license_server import LicenseServer
from lm_api.api.schemas.license_server import (
    LicenseServerCreateSchema,
    LicenseServerSchema,
    LicenseServerUpdateSchema,
)
from lm_api.constants import LicenseServerType
from lm_api.database import SecureSession, secure_session
from lm_api.permissions import Permissions

router = APIRouter()


crud_license_server = GenericCRUD(LicenseServer)


@router.get(
    "/types/",
    status_code=status.HTTP_200_OK,
    response_model=List[LicenseServerType],
)
async def get_license_server_types(
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_READ, commit=False)
    ),
):
    """Return a list of the available license server types."""
    return list(LicenseServerType)


@router.post(
    "",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_license_server(
    license_server: LicenseServerCreateSchema = Body(..., description="License server to be created"),
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_CREATE)
    ),
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
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_READ, commit=False)
    ),
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
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_READ, commit=False)
    ),
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
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_UPDATE)
    ),
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
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.LICENSE_SERVER_DELETE)
    ),
):
    """Delete a license server from the database."""
    return await crud_license_server.delete(db_session=secure_session.session, id=license_server_id)
