"""
Provide utilities that communicate with the backend.
"""
from typing import List, Optional

from fastapi import status
from httpx import ConnectError
from pydantic import BaseModel, ValidationError

from lm_agent.forward import async_client
from lm_agent.logs import logger

GET_CONFIG_URL_PATH = "/api/v1/config/all"


class LicenseManagerBackendConnectionError(Exception):
    """Exception for backend connection issues."""


class LicenseManagerBackendVersionError(Exception):
    """Exception for backend/agent version mismatches."""


async def get_license_manager_backend_version() -> str:
    """Return the license-manager-backend version."""
    resp = await async_client().get("/version")
    # Check that we have a valid response.
    if resp.status_code != status.HTTP_200_OK:
        logger.error("license-manager-backend version could not be obtained.")
        raise LicenseManagerBackendConnectionError()
    return resp.json()["version"]


class BackendConfigurationRow(BaseModel):
    """
    NOTE: This is a copy of the schema from the backend.
          If the schema changes upstream in a non-reverse-compatible
          way, this schema should cause errors in deserialization.
    """

    class Config:
        extra = "ignore"

    product: str
    features: List[str]
    license_servers: List[str]
    license_server_type: str
    grace_time: int


class BackendBookingRow(BaseModel):
    """
    NOTE: This is a copy of the schema from the backend.
          If the schema changes upstream in a non-reverse-compatible
          way, this schema should cause errors in deserialization.
    """

    class Config:
        extra = "ignore"

    job_id: str
    product_feature: str
    booked: int
    config_id: int
    lead_host: str
    user_name: str
    cluster_name: str


async def get_bookings_from_backend(cluster_name: Optional[str] = None) -> List[BackendBookingRow]:
    client = async_client()
    bookings: List = []
    try:
        if cluster_name:
            resp = await client.get(f"/api/v1/booking/all?cluster_name={cluster_name}")
        else:
            resp = await client.get("/api/v1/booking/all")
    except ConnectError as e:
        logger.error(f"Connection failed to backend: {e}")
        return bookings
    for booking in resp.json():
        try:
            bookings.append(BackendBookingRow.parse_obj(booking))
        except ValidationError as err:
            logger.error(f"Wrong format for booking: {str(err)}")
    return bookings


async def get_config_from_backend() -> List[BackendConfigurationRow]:
    client = async_client()
    path = GET_CONFIG_URL_PATH

    try:
        resp = await async_client().get(path)
    except ConnectError as e:
        logger.error(f"Connection failed to backend: {client.base_url}{path}: {e}")
        return []

    configs = []
    for (i, config_row) in enumerate(resp.json()):
        try:
            configs.append(BackendConfigurationRow.parse_obj(config_row))
        except ValidationError as err:
            logger.error(f"Could not validate config entry at row {i}: {str(err)}")
    return configs
