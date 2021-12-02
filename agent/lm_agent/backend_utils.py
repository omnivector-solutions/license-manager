"""
Provide utilities that communicate with the backend.
"""
import typing

import httpx
from pydantic import BaseModel, ValidationError

from lm_agent.config import settings
from lm_agent.exceptions import LicenseManagerAuthTokenError, LicenseManagerBackendConnectionError
from lm_agent.logs import logger


def acquire_token():
    """
    Retrieves a token from Auth0 based on the app settings.
    """
    logger.debug("Attempting to acquire token from Auth0 with config")
    auth0_body = dict(
        audience=settings.AUTH0_AUDIENCE,
        client_id=settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
        grant_type="client_credentials",
    )
    auth0_url = f"https://{settings.AUTH0_DOMAIN}/oauth/token"
    logger.debug(f"Posting Auth0 request to {auth0_url}")
    response = httpx.post(auth0_url, data=auth0_body)
    LicenseManagerAuthTokenError.require_condition(
        response.status_code == 200, f"Failed to get auth token from Auth0: {response.text}"
    )
    with LicenseManagerAuthTokenError.handle_errors("Malformed response payload from Auth0"):
        token = response.json()["access_token"]

    logger.debug("Successfully acquired auth token from Auth0")
    return token


class AsyncBackendClient(httpx.AsyncClient):
    """
    Extends the httpx.AsyncClient class with automatic token acquisition for requests.
    The token is acquired lazily on the first httpx request issued.

    This client should be used for most agent actions.
    """

    _token: typing.Optional[str]

    def __init__(self):
        self._token = None
        super().__init__(base_url=settings.BACKEND_BASE_URL, auth=self._inject_token)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


backend_client = AsyncBackendClient()


class SyncBackendClient(httpx.Client):
    """
    Extends the synchronous httpx.Client class with automatic token acquisition for requests.
    The token is acquired lazily on the first httpx request issued.

    This client should be used only for the CLI tools.
    """

    _token: typing.Optional[str]

    def __init__(self):
        self._token = None
        super().__init__(base_url=settings.BACKEND_BASE_URL, auth=self._inject_token)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


async def get_license_manager_backend_version() -> str:
    """Return the license-manager-backend version."""
    resp = await backend_client.get("/lm/version")
    # Check that we have a valid response.
    if resp.status_code != 200:
        logger.error("license-manager-backend version could not be obtained.")
        raise LicenseManagerBackendConnectionError("Could not obtain version from backend")
    return resp.json()["version"]


class BackendConfigurationRow(BaseModel):
    """
    NOTE: This is a copy of the schema from the backend.
          If the schema changes upstream in a non-reverse-compatible
          way, this schema should cause errors in deserialization.
    """

    class Config:
        extra = "ignore"

    id: typing.Optional[int] = None
    product: str
    features: dict
    license_servers: typing.List[str]
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


async def get_bookings_from_backend(
    cluster_name: typing.Optional[str] = None,
) -> typing.List[BackendBookingRow]:
    bookings: typing.List = []
    try:
        if cluster_name:
            resp = await backend_client.get(f"/lm/api/v1/booking/all?cluster_name={cluster_name}")
        else:
            resp = await backend_client.get("/lm/api/v1/booking/all")
    except httpx.ConnectError as e:
        logger.error(f"Connection failed to backend: {e}")
        return bookings
    for booking in resp.json():
        try:
            bookings.append(BackendBookingRow.parse_obj(booking))
        except ValidationError as err:
            logger.error(f"Wrong format for booking: {str(err)}")
    return bookings


async def get_config_id_from_backend(product_feature: str) -> int:
    """Given the product_feature return return the config id."""
    path = "/lm/api/v1/config/"
    resp = await backend_client.get(path, params={"product_feature": product_feature})
    return resp.json()


async def get_config_from_backend() -> typing.List[BackendConfigurationRow]:
    """Get all config rows from the backend."""
    path = "/lm/api/v1/config/all"

    try:
        resp = await backend_client.get(path)
    except httpx.ConnectError as e:
        logger.error(f"Connection failed to backend: {backend_client.base_url}{path}: {e}")
        return []

    configs = []
    for (i, config_row) in enumerate(resp.json()):
        try:
            configs.append(BackendConfigurationRow.parse_obj(config_row))
        except ValidationError as err:
            logger.error(f"Could not validate config entry at row {i}: {str(err)}")
    return configs
