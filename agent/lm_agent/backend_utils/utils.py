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
    """
    Hit the API's health-check endpoint to make sure the API is available.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/health")
    if resp.status_code != 204:
        logger.error("license-manager-backend health-check failed.")
        raise LicenseManagerBackendConnectionError("Could not connect to the backend health-check endpoint")


async def get_jobs_from_backend() -> Optional[List[JobSchema]]:
    """
    Get all jobs for the cluster with its bookings from the backend.
    """
    cluster_data = await get_cluster_from_backend()
    if cluster_data:
        return cluster_data.jobs
    return []


async def get_configs_from_backend() -> Optional[List[ConfigurationSchema]]:
    """
    Get all config rows from the backend.
    """
    cluster_data = await get_cluster_from_backend()
    if cluster_data:
        return cluster_data.configurations
    return []


async def get_all_clusters_from_backend() -> Optional[List[ClusterSchema]]:
    """
    Get all clusters from the backend.
    """
    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.get("/lm/clusters")

        LicenseManagerBackendConnectionError.require_condition(
            resp.status_code == 200, f"Could not get cluster data from the backend: {resp.text}"
        )

    parsed_resp: List = resp.json()

    clusters = []

    for cluster in parsed_resp:
        try:
            parsed_cluster = ClusterSchema.parse_obj(cluster)
        except ValidationError as err:
            logger.error(f"Could not validate cluster data: {str(err)}")
            raise LicenseManagerParseError("Could not parse cluster data returned from the backend")

        clusters.append(parsed_cluster)

    return clusters


async def get_cluster_from_backend() -> ClusterSchema:
    """
    Get cluster data from the backend.
    """
    try:
        async with AsyncBackendClient() as backend_client:
            resp = await backend_client.get("/lm/clusters/by_client_id")
    except httpx.ConnectError as err:
        logger.error(f"Connection failed to backend: {str(err)}")
        raise LicenseManagerBackendConnectionError("Could not get cluster data from the backend")

    parsed_resp: dict = resp.json()

    try:
        cluster_data = ClusterSchema.parse_obj(parsed_resp)
    except ValidationError as err:
        logger.error(f"Could not validate cluster data: {str(err)}")
        raise LicenseManagerParseError("Could not parse cluster data returned from the backend")

    return cluster_data


def get_feature_ids(cluster_data: ClusterSchema) -> Dict[str, int]:
    """
    Get the feature_id for each product_feature in the cluster.
    """
    features_id = {
        f"{feature.product.name}.{feature.name}": feature.id
        for configuration in cluster_data.configurations
        for feature in configuration.features
    }

    return features_id


def get_inventory_ids(cluster_data: ClusterSchema) -> Dict[str, int]:
    """
    Get the inventory_id for each product_feature in the cluster.
    """
    inventories_id = {
        f"{feature.product.name}.{feature.name}": feature.inventory.id
        for configuration in cluster_data.configurations
        for feature in configuration.features
    }

    return inventories_id


def get_grace_times(cluster_data: ClusterSchema) -> Dict[int, int]:
    """
    Get the grace time for each feature_id in the cluster.
    """
    grace_times = {
        feature.id: configuration.grace_time
        for configuration in cluster_data.configurations
        for feature in configuration.features
    }

    return grace_times


async def make_inventory_update(inventory_id: int, total: int, used: int) -> bool:
    """
    Update the inventory for a feature with its current counters.
    """
    async with AsyncBackendClient() as backend_client:
        inventory_response = await backend_client.put(
            f"/lm/inventories/{inventory_id}",
            json={
                "total": total,
                "used": used,
            },
        )
        LicenseManagerBackendConnectionError.require_condition(
            inventory_response.status_code == 200, f"Failed to update inventory: {inventory_response.text}"
        )
    return True


async def make_booking_request(lbr: LicenseBookingRequest) -> bool:
    """
    Create a job and its bookings on the backend for each license booked.
    """
    cluster_data = await get_cluster_from_backend()

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
            LicenseManagerBackendConnectionError.require_condition(
                booking_response.status_code == 201, f"Failed to create booking: {booking_response.text}"
            )

    logger.debug("##### Booking completed successfully #####")
    return True


async def remove_job_by_slurm_job_id(slurm_job_id: str) -> bool:
    """
    Remove the job with its bookings for the given slurm_job_id in the cluster.
    """
    cluster_data = await get_cluster_from_backend()

    async with AsyncBackendClient() as backend_client:
        resp = await backend_client.delete(
            f"lm/jobs/slurm_job_id/{slurm_job_id}/cluster_id/{cluster_data.id}"
        )

        LicenseManagerBackendConnectionError.require_condition(
            resp.status_code == 200, f"Failed to remove job: {resp.text}"
        )

    logger.debug("##### Job removed successfully #####")
    return True


async def get_bookings_for_job_id(slurm_job_id: str) -> Dict:
    """
    Return the job with its bookings for the given job_id in the cluster.
    """
    cluster_data = await get_cluster_from_backend()

    async with AsyncBackendClient() as backend_client:
        job_response = await backend_client.get(
            f"/lm/jobs/by_slurm_id/{slurm_job_id}/cluster/{cluster_data.id}"
        )

        LicenseManagerBackendConnectionError.require_condition(
            job_response.status_code == 200, f"Failed to get job: {job_response.text}"
        )

        with LicenseManagerParseError.handle_errors(""):
            parsed_resp: List = job_response.json()["bookings"]

    bookings = []

    for booking in parsed_resp:
        try:
            parsed_booking = BookingSchema.parse_obj(booking)
        except ValidationError as err:
            logger.error(f"Could not validate booking data: {str(err)}")
            raise LicenseManagerParseError("Could not parse booking data returned from the backend")

        bookings.append(parsed_booking)

    return bookings


async def get_bookings_sum_per_cluster(product_feature: str) -> Dict[int, int]:
    """
    Get booking sum for a license's bookings in each cluster.
    """
    # get all clusters data
    clusters = await get_all_clusters_from_backend()

    booking_sum: Dict[int, int] = {}

    # get feature_ids in each cluster
    for cluster in clusters:
        cluster_feature_ids = get_feature_ids(cluster)
        feature_id = cluster_feature_ids.get(product_feature)

        if feature_id is not None:
            for job in cluster.jobs:
                for booking in job.bookings:
                    if booking.feature_id == feature_id:
                        booking_sum[cluster.id] = booking_sum.get(cluster.id, 0) + booking.quantity

    return booking_sum