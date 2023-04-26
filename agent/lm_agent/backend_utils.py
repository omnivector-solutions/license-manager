"""
Provide utilities that communicate with the backend.
"""
import getpass
from typing import Dict, List, Optional, Union

import httpx
import jwt
from pydantic import BaseModel, Field, ValidationError

from lm_agent.config import PRODUCT_FEATURE_RX, settings
from lm_agent.exceptions import LicenseManagerAuthTokenError, LicenseManagerBackendConnectionError
from lm_agent.logs import logger

USER_NAME = getpass.getuser()
TOKEN_FILE_NAME = f"{USER_NAME}.token"


def _load_token_from_cache() -> Union[str, None]:
    """
    Looks for and returns a token from a cache file (if it exists).

    Returns None if::
    * The token does not exist
    * Can't read the token
    * The token is expired (or will expire within 10 seconds)
    """
    token_path = settings.CACHE_DIR / TOKEN_FILE_NAME
    if not token_path.exists():
        return None

    try:
        token = token_path.read_text()
    except Exception as err:
        logger.warning(f"Couldn't load token from cache file {token_path}. Will acquire a new one: {err}")
        return None

    try:
        jwt.decode(token, options=dict(verify_signature=False, verify_exp=True), leeway=-10)
    except jwt.ExpiredSignatureError:
        logger.warning("Cached token is expired. Will acquire a new one.")
        return None

    logger.debug(f"Successfully loaded token from cache file {token_path}.")
    return token


def _write_token_to_cache(token: str):
    """
    Writes the token to the cache.
    """
    cache_dir = settings.CACHE_DIR
    if not cache_dir.exists():
        logger.warning(f"Cache directory does not exist {cache_dir}. Token won't be saved.")
        return

    token_path = settings.CACHE_DIR / TOKEN_FILE_NAME
    try:
        token_path.write_text(token)
        token_path.chmod(0o600)
        logger.debug(f"Successfully saved token to {token_path}")
    except Exception as err:
        logger.warning(f"Couldn't save token to {token_path}: {err}")


def acquire_token() -> str:
    """
    Retrieves a token from OIDC based on the app settings.
    """
    logger.debug("Attempting to use cached token")
    token = _load_token_from_cache()

    if token is None:
        logger.debug("Attempting to acquire token from OIDC")
        oidc_body = dict(
            audience=settings.OIDC_AUDIENCE,
            client_id=settings.OIDC_CLIENT_ID,
            client_secret=settings.OIDC_CLIENT_SECRET,
            grant_type="client_credentials",
        )
        oidc_url = f"https://{settings.OIDC_DOMAIN}/protocol/openid-connect/token"
        logger.debug(f"Posting OIDC request to {oidc_url}")
        response = httpx.post(oidc_url, data=oidc_body)
        LicenseManagerAuthTokenError.require_condition(
            response.status_code == 200, f"Failed to get auth token from OIDC: {response.text}"
        )
        with LicenseManagerAuthTokenError.handle_errors("Malformed response payload from OIDC"):
            token = response.json()["access_token"]

        logger.debug("Successfully acquired auth token from OIDC")
        _write_token_to_cache(token)

    return token


class AsyncBackendClient(httpx.AsyncClient):
    """
    Extends the httpx.AsyncClient class with automatic token acquisition for requests.
    The token is acquired lazily on the first httpx request issued.

    This client should be used for most agent actions.
    """

    _token: Optional[str]

    def __init__(self):
        self._token = None
        super().__init__(base_url=settings.BACKEND_BASE_URL, auth=self._inject_token)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


class SyncBackendClient(httpx.Client):
    """
    Extends the synchronous httpx.Client class with automatic token acquisition for requests.
    The token is acquired lazily on the first httpx request issued.

    This client should be used only for the CLI tools.
    """

    _token: Optional[str]

    def __init__(self):
        self._token = None
        super().__init__(base_url=settings.BACKEND_BASE_URL, auth=self._inject_token)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


async def check_backend_health():
    """Hit the API's health-check endpoint to make sure the API is available."""
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/health")
    if resp.status_code != 204:
        logger.error("license-manager-backend health-check failed.")
        raise LicenseManagerBackendConnectionError("Could not connect to the backend health-check endpoint")


class BackendConfigurationRow(BaseModel):
    """
    NOTE: This is a copy of the schema from the backend.
          If the schema changes upstream in a non-reverse-compatible way, this schema should cause errors
          in deserialization.
    """

    class Config:
        extra = "ignore"

    id: Optional[int] = None
    product: str
    features: dict
    license_servers: List[str]
    license_server_type: str
    grace_time: int
    client_id: str


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


class LicenseBooking(BaseModel):
    """
    Structure to represent a license booking.
    """

    product_feature: str = Field(..., regex=PRODUCT_FEATURE_RX)
    tokens: int
    license_server_type: Union[None, str]


class LicenseBookingRequest(BaseModel):
    """
    Structure to represent a list of license bookings.
    """

    job_id: int
    bookings: Union[List, List[LicenseBooking]]
    user_name: str
    lead_host: str
    cluster_name: str


async def get_bookings_from_backend(
    cluster_name: Optional[str] = None,
) -> List[BackendBookingRow]:
    bookings: List = []
    try:
        async with AsyncBackendClient() as backend_client:
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
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get(path, params={"product_feature": product_feature})
    return resp.json()


async def get_config_from_backend() -> List[BackendConfigurationRow]:
    """Get all config rows from the backend."""
    path = "/lm/api/v1/config/agent/all"

    try:
        async with AsyncBackendClient() as backend_client:
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


async def make_booking_request(lbr: LicenseBookingRequest) -> bool:
    """Book the feature tokens."""

    features = [
        {
            "product_feature": license_booking.product_feature,
            "booked": license_booking.tokens,
        }
        for license_booking in lbr.bookings
    ]

    logger.debug(f"features: {features}")
    logger.debug(f"lbr: {lbr}")

    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.put(
            "/lm/api/v1/booking/book",
            json={
                "job_id": lbr.job_id,
                "features": features,
                "user_name": lbr.user_name,
                "lead_host": lbr.lead_host,
                "cluster_name": lbr.cluster_name,
            },
        )

    if resp.status_code == 200:
        logger.debug("##### Booking completed successfully #####")
        return True
    logger.debug(f"##### Booking failed: {str(resp.content)} #####")
    return False


async def remove_booking_for_job_id(job_id: str) -> bool:
    """Remove token bookings used by job."""

    # Remove the booking for the job.
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.delete(f"lm/api/v1/booking/book/{job_id}")
    # Return True if the request to delete the booking was successful.
    if resp.status_code == 200:
        return True
    logger.error(f"{job_id} could not be deleted.")
    logger.debug(f"response from delete: {resp.__dict__}")
    return False


async def get_all_grace_times() -> Dict[int, int]:
    """
    Send GET to /lm/api/v1/config/all.
    """
    async with AsyncBackendClient() as backend_client:
        response = await backend_client.get("/lm/api/v1/config/all")
    configs = response.json()
    grace_times = {config["id"]: config["grace_time"] for config in configs}
    return grace_times


async def get_booking_for_job_id(job_id: str) -> Dict:
    """
    Return the booking row for the given job_id.
    """
    async with AsyncBackendClient() as backend_client:
        response = await backend_client.get(f"/lm/api/v1/booking/job/{job_id}")
    return response.json()


async def get_bookings_sum_per_cluster(product_feature: str) -> Dict[str, int]:
    """
    Get booking sum for a license's bookings in each cluster.
    """
    async with AsyncBackendClient() as backend_client:
        response = await backend_client.get("/lm/api/v1/booking/all")
    bookings = response.json()

    booking_sum: Dict[str, int] = {}

    for booking in bookings:
        cluster_name = booking["cluster_name"]
        if booking["product_feature"] == product_feature:
            booking_sum[cluster_name] = booking_sum.get(cluster_name, 0) + booking["booked"]

    return booking_sum
