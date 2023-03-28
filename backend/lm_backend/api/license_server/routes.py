from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status

from lm_backend.api.license_server.crud import LicenseServerCRUD
from lm_backend.api.license_server.dependencies import get_license_server_crud
from lm_backend.api.license_server.schemas import LicenseServerCreateRequest, LicenseServerResponse

router = APIRouter()


@router.post("/", response_model=LicenseServerResponse)
async def create_license_server(
    license_server: LicenseServerCreateRequest,
    license_server_crud: LicenseServerCRUD = Depends(get_license_server_crud),
):
    """Create a new license server."""
    try:
        return license_server_crud.create(license_server=license_server)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[LicenseServerResponse])
async def read_all_license_servers(license_server_crud: LicenseServerCRUD = Depends(get_license_server_crud)):
    """Return all license servers."""
    return await license_server_crud.read_all()


@router.get("/{license_server_id}", response_model=LicenseServerResponse)
async def read_license_server(
    license_server_id: int, license_server_crud: LicenseServerCRUD = Depends(get_license_server_crud)
):
    """Return a license server with the given id."""
    license_server = await license_server_crud.read(license_server_id=license_server_id)
    if not license_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License server not found")

    return license_server


@router.put("/{license_server_id}", response_model=LicenseServerResponse)
async def update_license_server(
    license_server_id: int,
    host: Optional[str] = Body(None),
    port: Optional[int] = Body(None),
    type: Optional[str] = Body(None),
    license_server_crud: LicenseServerCRUD = Depends(get_license_server_crud),
):
    """Update a license server in the database."""
    license_server = await license_server_crud.read(license_server_id)
    if not license_server:
        raise HTTPException(status_code=404, detail="License server not found")

    try:
        return await license_server_crud.update(
            license_server_id=license_server_id, host=host, port=port, type=type
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{license_server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_license_server(
    license_server_id: int, license_server_crud: LicenseServerCRUD = Depends(get_license_server_crud)
):
    """Delete a license server from the database."""
    license_server = await license_server_crud.read(license_server_id)
    if not license_server:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License server not found")
    try:
        deleted = license_server_crud.delete(license_server_id=license_server_id)
        if deleted:
            return status.HTTP_204_NO_CONTENT
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
