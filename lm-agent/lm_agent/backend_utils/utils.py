"""
Provide utilities that communicate with the backend.
"""
import getpass
from typing import Dict, List, Optional, Union

import httpx
import jwt

from lm_agent.models import (
    ConfigurationSchema,
    FeatureSchema,
    JobSchema,
    LicenseBookingRequest,
)
from lm_agent.config import settings
from lm_agent.exceptions import (
    LicenseManagerAuthTokenError,
    LicenseManagerBackendConnectionError,
    LicenseManagerParseError,
)
from lm_agent.logs import log_error, logger

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
            client_id=settings.OIDC_CLIENT_ID,
            client_secret=settings.OIDC_CLIENT_SECRET,
            grant_type="client_credentials",
        )
        protocol = "https" if settings.OIDC_USE_HTTPS else "http"
        oidc_url = f"{protocol}://{settings.OIDC_DOMAIN}/protocol/openid-connect/token"
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
        super().__init__(base_url=str(settings.BACKEND_BASE_URL), auth=self._inject_token, timeout=None)

    def _inject_token(self, request: httpx.Request) -> httpx.Request:
        if self._token is None:
            self._token = acquire_token()
        request.headers["authorization"] = f"Bearer {self._token}"
        return request


async def check_backend_health():
    """
    Hit the API's health-check endpoint to make sure the API is available.
    """
    logger.debug("Checking backend health")
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/health")
    if resp.status_code != 204:
        logger.error(f"Backend health-check request failed with status code: {resp.status_code}")
        raise LicenseManagerBackendConnectionError("Could not connect to the backend health-check endpoint")
    logger.debug("Backend is healthy!")


async def report_cluster_status():
    """
    Report the cluster status to the backend.
    """
    logger.debug("Reporting cluster status")
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.put("/lm/cluster_statuses", params={"interval": settings.STAT_INTERVAL})

    LicenseManagerBackendConnectionError.require_condition(
        resp.status_code == 202, f"Failed to report cluster status: {resp.text}"
    )
    logger.debug("Cluster status reported successfully")


async def get_cluster_jobs_from_backend() -> List[JobSchema]:
    """
    Get all jobs for the cluster with its bookings from the backend.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/jobs/by_client_id")

        LicenseManagerBackendConnectionError.require_condition(
            resp.status_code == 200, f"Could not get job data from the backend: {resp.text}"
        )

    parsed_resp: List = resp.json()

    with LicenseManagerParseError.handle_errors(
        "Could not parse job data returned from the backend", do_except=log_error
    ):
        jobs = [JobSchema.model_validate(job) for job in parsed_resp]

    return jobs


async def get_cluster_configs_from_backend() -> List[ConfigurationSchema]:
    """
    Get all configs from the backend for the cluster.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/configurations/by_client_id")

        LicenseManagerBackendConnectionError.require_condition(
            resp.status_code == 200, f"Could not get configuration data from the backend: {resp.text}"
        )

    parsed_resp: List = resp.json()

    with LicenseManagerParseError.handle_errors(
        "Could not parse configuration data returned from the backend", do_except=log_error
    ):
        configurations = [ConfigurationSchema.model_validate(configuration) for configuration in parsed_resp]

    return configurations


async def make_feature_update(features_to_update: List[Dict]):
    """
    Update the feature with its current counters.
    """
    async with AsyncBackendClient() as backend_client:
        features_response = await backend_client.put(
            "/lm/features/bulk",
            json=features_to_update,
        )
        LicenseManagerBackendConnectionError.require_condition(
            features_response.status_code == 200, f"Failed to update feature: {features_response.text}"
        )


async def make_booking_request(lbr: LicenseBookingRequest) -> bool:
    """
    Create a job and its bookings on the backend for each license booked.
    """
    async with AsyncBackendClient() as backend_client:
        job_response = await backend_client.post(
            "/lm/jobs",
            json=lbr.model_dump(),
        )
        if job_response.status_code != 201:
            logger.error(f"Failed to create booking: {job_response.text}")
            return False

    logger.debug(f"##### Job {lbr.slurm_job_id} created successfully #####")
    return True


async def remove_job_by_slurm_job_id(slurm_job_id: str):
    """
    Remove the job with its bookings for the given slurm_job_id in the cluster.

    If the job doesn't exist, the request will be ignored.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.delete(f"lm/jobs/slurm_job_id/{slurm_job_id}")

        LicenseManagerBackendConnectionError.require_condition(
            resp.status_code in [200, 404], f"Failed to remove job: {resp.text}"
        )

    logger.debug(f"##### Job {slurm_job_id} removed successfully #####")


async def remove_booking(booking_id: int):
    """
    Remove the booking with the given id.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.delete(f"lm/bookings/{booking_id}")

    LicenseManagerBackendConnectionError.require_condition(
        resp.status_code == 200, f"Failed to remove booking: {resp.text}"
    )

    logger.debug(f"##### Booking {booking_id} removed successfully")


async def get_all_features_from_backend() -> List[FeatureSchema]:
    """
    Return the job with its bookings for the given job_id in the cluster.
    """
    async with AsyncBackendClient() as backend_client:
        feature_response = await backend_client.get("/lm/features")

        LicenseManagerBackendConnectionError.require_condition(
            feature_response.status_code == 200, f"Failed to get features: {feature_response.text}"
        )

        with LicenseManagerParseError.handle_errors(""):
            parsed_resp: List = feature_response.json()

    with LicenseManagerParseError.handle_errors(
        "Could not parse feature data returned from the backend", do_except=log_error
    ):
        features = [FeatureSchema.model_validate(feature) for feature in parsed_resp]

    return features


async def get_all_features_bookings_sum() -> Dict[str, int]:
    """
    Get booking sum for a license's bookings in all clusters.

    Note: a license can be configured in multiple clusters,
    having the same name but different configurations.

    The booking sum is the sum of all bookings for a license in all clusters.
    """
    # get all features
    features = await get_all_features_from_backend()
    all_product_features = [f"{feature.product.name}.{feature.name}" for feature in features]

    # sum bookings for each feature with the same name
    bookings_sum = {
        product_feature: sum(
            feature.booked_total
            for feature in features
            if f"{feature.product.name}.{feature.name}" == product_feature
        )
        for product_feature in all_product_features
    }

    return bookings_sum
