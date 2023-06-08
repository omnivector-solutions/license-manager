"""
Provide utilities that communicate with the backend.
"""
import getpass
from typing import Dict, List, Optional, Union

import httpx
import jwt
from pydantic import ValidationError

from lm_agent.backend_utils.models import (
    BookingSchema,
    ClusterSchema,
    ConfigurationSchema,
    JobSchema,
    LicenseBookingRequest,
)
from lm_agent.config import settings
from lm_agent.exceptions import (
    LicenseManagerAuthTokenError,
    LicenseManagerBackendConnectionError,
    LicenseManagerParseError,
)
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


async def check_backend_health():
    """Hit the API's health-check endpoint to make sure the API is available."""
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/health")
    if resp.status_code != 204:
        logger.error("license-manager-backend health-check failed.")
        raise LicenseManagerBackendConnectionError("Could not connect to the backend health-check endpoint")


async def get_bookings_from_backend() -> List[BookingSchema]:
    cluster_data = get_cluster_from_backend()
    return cluster_data.bookings


async def get_jobs_from_backend() -> List[JobSchema]:
    cluster_data = get_cluster_from_backend()
    return cluster_data.jobs


async def get_cluster_from_backend() -> ClusterSchema:
    """Get cluster data from the backend."""
    try:
        async with AsyncBackendClient() as backend_client:
            resp = await backend_client.get("/lm/api/v1/clusters/by_client_id/")
    except httpx.ConnectError as err:
        logger.error(f"Connection failed to backend: {str(err)}")
        raise LicenseManagerBackendConnectionError("Could not get cluster data from the backend")

    parsed_resp: dict = resp.json()

    try:
        cluster_data = ClusterSchema.parse_obj(parsed_resp)
    except ValidationError as err:
        logger.error(f"Could not validate cluster data: {str(err)}")
        raise LicenseManagerParseError("Could not parse configuration data returned from the backend")

    return cluster_data


async def get_configs_from_backend() -> List[ConfigurationSchema]:
    """Get all config rows from the backend."""
    cluster_data = get_cluster_from_backend()
    return cluster_data.configurations


def get_feature_ids(cluster_data) -> Dict[str, int]:
    """Get the feature_id for each feature in the cluster."""
    features_id = {
        f"{feature.product.name}.{feature.name}": feature.id
        for configuration in cluster_data.configurations
        for feature in configuration.features
    }

    return features_id


def get_grace_times(cluster_data) -> Dict[int, int]:
    """Get the grace time for each feature_id in the cluster."""
    grace_times = {
        feature.id: configuration.grace_time
        for configuration in cluster_data.configurations
        for feature in configuration.features
    }

    return grace_times


async def make_booking_request(lbr: LicenseBookingRequest) -> bool:
    """Book the feature tokens."""
    cluster_data = get_cluster_from_backend()

    async with AsyncBackendClient() as backend_client:
        job_response = await backend_client.post(
            "/lm/jobs",
            json={
                "slurm_job_id": lbr.slurm_job_id,
                "cluster_id": cluster_data.id,
                "user_name": lbr.user_name,
                "lead_host": lbr.lead_host,
            },
        )
        LicenseManagerBackendConnectionError.require_condition(
            job_response.status_code == 201, f"Failed to create job: {job_response.text}"
        )

    with LicenseManagerParseError.handle_errors("Could not get job_id from created job"):
        job_id = job_response.json()["id"]

    features_id = get_feature_ids(cluster_data)
    for booking in lbr.bookings:
        async with AsyncBackendClient() as backend_client:
            booking_response = await backend_client.post(
                "/lm/bookings",
                json={
                    "job_id": job_id,
                    "feature_id": features_id[booking.product_feature],
                    "quantity": booking.quantity,
                },
            )

        if booking_response.status_code != 201:
            logger.error(f"##### Booking failed: {str(booking_response.content)} #####")
            return False

    logger.debug("##### Booking completed successfully #####")
    return True


async def remove_job_by_slurm_job_id(slurm_job_id: str) -> bool:
    """
    Remove the job with its bookings for the given slurm_job_id in the cluster.
    """
    cluster_data = get_cluster_from_backend()

    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.delete(
            f"lm/jobs/slurm_job_id/{slurm_job_id}/cluster_id/{cluster_data.id}"
        )

    # Return True if the request to delete the job with the bookings was successful.
    if resp.status_code == 200:
        return True

    logger.error(f"{slurm_job_id} could not be deleted.")
    logger.debug(f"response from delete: {resp.__dict__}")
    return False


async def get_bookings_for_job_id(slurm_job_id: str) -> Dict:
    """
    Return the job with its bookings for the given job_id in the cluster.
    """
    cluster_data = get_cluster_from_backend()

    async with AsyncBackendClient() as backend_client:
        job_response = await backend_client.get(
            f"/lm/jobs/by_slurm_id/{slurm_job_id}/cluster/{cluster_data.id}"
        )
        bookings = job_response.json()["bookings"]

    return bookings


async def get_bookings_sum_per_cluster(product_feature: str) -> Dict[str, int]:
    """
    Get booking sum for a license's bookings in each cluster.
    """
    async with AsyncBackendClient() as backend_client:
        response = await backend_client.get("/lm/bookings")
    bookings = response.json()

    booking_sum: Dict[str, int] = {}

    for booking in bookings:
        cluster_name = booking["cluster_id"]
        if booking["product_feature"] == product_feature:
            booking_sum[cluster_name] = booking_sum.get(cluster_name, 0) + booking["booked"]

    return booking_sum
