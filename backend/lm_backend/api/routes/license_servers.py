from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models import LicenseServer
from lm_backend.api.schemas import LicenseServerCreateSchema, LicenseServerSchema, LicenseServerUpdateSchema
from lm_backend.permissions import Permissions
from lm_backend.security import guard
from lm_backend.session import get_session

router = APIRouter()


crud_license_server = GenericCRUD(LicenseServer, LicenseServerCreateSchema, LicenseServerUpdateSchema)


@router.post(
    "/",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_SERVER_EDIT))],
)
async def create_license_server(
    license_server: LicenseServerCreateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Create a new license server."""
    return await crud_license_server.create(db_session=db_session, obj=license_server)


@router.get(
    "/",
    response_model=List[LicenseServerSchema],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_SERVER_VIEW))],
)
async def read_all_license_servers(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    db_session: AsyncSession = Depends(get_session),
):
    """Return all license servers."""
    return await crud_license_server.read_all(
        db_session=db_session, search=search, sort_field=sort_field, sort_ascending=sort_ascending
    )


@router.get(
    "/{license_server_id}",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_SERVER_VIEW))],
)
async def read_license_server(license_server_id: int, db_session: AsyncSession = Depends(get_session)):
    """Return a license server with the given id."""
    return await crud_license_server.read(db_session=db_session, id=license_server_id)


@router.put(
    "/{license_server_id}",
    response_model=LicenseServerSchema,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_SERVER_EDIT))],
)
async def update_license_server(
    license_server_id: int,
    license_server_update: LicenseServerUpdateSchema,
    db_session: AsyncSession = Depends(get_session),
):
    """Update a license server in the database."""
    return await crud_license_server.update(
        db_session=db_session,
        id=license_server_id,
        obj=license_server_update,
    )


@router.delete(
    "/{license_server_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(guard.lockdown(Permissions.LICENSE_SERVER_EDIT))],
)
async def delete_license_server(license_server_id: int, db_session: AsyncSession = Depends(get_session)):
    """Delete a license server from the database."""
    return await crud_license_server.delete(db_session=db_session, id=license_server_id)

