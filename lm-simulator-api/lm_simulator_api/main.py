from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from lm_simulator_api import __version__
from lm_simulator_api.constants import LicenseServerType
from lm_simulator_api.crud import (
    add_license,
    add_license_in_use,
    list_licenses,
    list_licenses_by_server_type,
    list_licenses_in_use,
    read_license_by_name,
    remove_license,
    remove_license_in_use,
)
from lm_simulator_api.database import get_session, init_db
from lm_simulator_api.schemas import LicenseCreate, LicenseInUseCreate, LicenseInUseRow, LicenseRow

subapp = FastAPI(
    title="License Manager Simulator API",
    version=__version__,
    contact={
        "name": "Omnivector Solutions",
        "url": "https://www.omnivector.solutions/",
        "email": "info@omnivector.solutions",
    },
    license_info={
        "name": "MIT License",
        "url": "https://github.com/omnivector-solutions/license-manager/blob/main/LICENSE",
    },
)

subapp.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@subapp.get(
    "/health",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={204: {"description": "API is healthy"}},
)
async def health():
    """
    Provide a health-check endpoint for the app.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@subapp.post(
    "/licenses",
    status_code=status.HTTP_201_CREATED,
    response_model=LicenseRow,
)
async def create_license(license: LicenseCreate, session: AsyncSession = Depends(get_session)):
    license = await add_license(session=session, license=license)
    return license


@subapp.get(
    "/licenses",
    status_code=status.HTTP_200_OK,
    response_model=List[LicenseRow],
)
async def get_licenses(session: AsyncSession = Depends(get_session)):
    licenses = await list_licenses(session=session)
    return licenses


@subapp.get(
    "/licenses/{license_name}",
    status_code=status.HTTP_200_OK,
    response_model=LicenseRow,
)
async def get_license_by_name(license_name: str, session: AsyncSession = Depends(get_session)):
    license = await read_license_by_name(session=session, license_name=license_name)
    return license


@subapp.get(
    "/licenses/type/{server_type}",
    status_code=status.HTTP_200_OK,
    response_model=List[LicenseRow],
)
async def get_licenses_by_server_type(
    server_type: LicenseServerType, session: AsyncSession = Depends(get_session)
):
    licenses = await list_licenses_by_server_type(session=session, server_type=server_type)
    return licenses


@subapp.delete(
    "/licenses/{license_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_license(
    license_name: str,
    session: AsyncSession = Depends(get_session),
):
    await remove_license(session=session, license_name=license_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@subapp.post(
    "/licenses-in-use",
    status_code=status.HTTP_201_CREATED,
    response_model=LicenseInUseRow,
)
async def create_license_in_use(
    license_in_use: LicenseInUseCreate, session: AsyncSession = Depends(get_session)
):
    license_in_use = await add_license_in_use(session=session, license_in_use=license_in_use)
    return license_in_use


@subapp.get(
    "/licenses-in-use",
    status_code=status.HTTP_200_OK,
    response_model=List[LicenseInUseRow],
)
async def get_licenses_in_use(session: AsyncSession = Depends(get_session)):
    licenses_in_use = await list_licenses_in_use(session=session)
    return licenses_in_use


@subapp.delete(
    "/licenses-in-use/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_license_in_use(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    await remove_license_in_use(session=session, id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()

    yield


app = FastAPI(lifespan=lifespan)
app.mount("/lm-sim", subapp)
