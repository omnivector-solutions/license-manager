#!/usr/bin/env python3
"""
Reconciliation functionality live here.
"""
import asyncio
from typing import Dict, List

from httpx import ConnectError

from lm_agent.backend_utils import backend_client, get_bookings_from_backend, get_config_id_from_backend
from lm_agent.exceptions import (
    LicenseManagerBackendConnectionError,
    LicenseManagerEmptyReportError,
    LicenseManagerFeatureConfigurationIncorrect,
    LicenseManagerReservationFailure,
)
from lm_agent.license_report import report
from lm_agent.logs import logger
from lm_agent.workload_managers.slurm.cmd_utils import (
    get_all_product_features_from_cluster,
    get_cluster_name,
    get_tokens_for_license,
    return_formatted_squeue_out,
    squeue_parser,
)
from lm_agent.workload_managers.slurm.reservations import (
    scontrol_create_reservation,
    scontrol_delete_reservation,
    scontrol_show_reservation,
    scontrol_update_reservation,
)

RECONCILE_URL_PATH = "/lm/api/v1/license/reconcile"


async def remove_booked_for_job_id(job_id: str):
    """
    Send DELETE to /lm/api/v1/booking/book/{job_id}.
    """
    response = await backend_client.delete(f"/lm/api/v1/booking/book/{job_id}")
    if response.status_code != 200:
        logger.error(f"{job_id} could not be deleted.")
        logger.debug(f"response from delete: {response.__dict__}")


async def get_all_grace_times() -> Dict[int, int]:
    """
    Send GET to /lm/api/v1/config/all.
    """
    response = await backend_client.get("/lm/api/v1/config/all")
    configs = response.json()
    grace_times = {config["id"]: config["grace_time"] for config in configs}
    return grace_times


async def get_booked_for_job_id(job_id: str) -> Dict:
    """
    Return the booking row for the given job_id.
    """
    response = await backend_client.get(f"/lm/api/v1/booking/job/{job_id}")
    return response.json()


def get_greatest_grace_time(job_id: str, grace_times: Dict[int, int], booking_rows: List) -> int:
    """
    Find the greatest grace_time for the given job_id.
    """
    greatest_grace_time = -1
    for book in booking_rows:
        if not book:
            continue
        for inner_book in book:
            if str(inner_book["job_id"]) != str(job_id):
                continue
            config_id_for_grace_times = inner_book["config_id"]
            greatest_grace_time = max(greatest_grace_time, grace_times[config_id_for_grace_times])
    return greatest_grace_time


def get_running_jobs(squeue_result: List) -> List:
    return [j for j in squeue_result if j["state"] == "RUNNING"]


async def clean_booked_grace_time():
    """
    Clean the booked licenses if the job's running time is greater than the grace_time.
    """
    logger.debug("GRACE_TIME START")
    formatted_squeue_output = return_formatted_squeue_out()
    cluster_name = await get_cluster_name()
    if not formatted_squeue_output:
        logger.debug("GRACE_TIME no squeue")
        await clean_bookings(None, cluster_name)
        logger.debug("GRACE_TIME cleaned bookings that are not in the queue")
        return
    squeue_result = squeue_parser(formatted_squeue_output)
    squeue_running_jobs = get_running_jobs(squeue_result)

    grace_times = await get_all_grace_times()
    get_booked_call = []
    for job in squeue_running_jobs:
        job_id = job["job_id"]
        get_booked_call.append(get_booked_for_job_id(job_id))

    booking_rows_for_running_jobs = await asyncio.gather(*get_booked_call)

    # get the greatest grace_time for each job
    for job in squeue_running_jobs:
        job_id = job["job_id"]
        greatest_grace_time = get_greatest_grace_time(job_id, grace_times, booking_rows_for_running_jobs)
        # if the running_time is greater than the greatest grace_time, delete the booking for it
        if job["run_time_in_seconds"] > greatest_grace_time and greatest_grace_time != -1:
            logger.debug(f"GRACE_TIME: {greatest_grace_time}, {job_id}")
            await remove_booked_for_job_id(job_id)
    await clean_bookings(squeue_result, cluster_name)


async def clean_bookings(squeue_result, cluster_name):
    logger.debug("CLEAN_BOOKINGS: start")
    cluster_bookings = [str(booking.job_id) for booking in await get_bookings_from_backend(cluster_name)]
    if squeue_result is None:
        squeue_result = []
    jobs_not_running = [str(job["job_id"]) for job in squeue_result if job["state"] != "RUNNING"]
    all_jobs_squeue = [str(job["job_id"]) for job in squeue_result]
    delete_booking_call = []
    logger.debug("CLEAN_BOOKINGS: after building lists")
    for job_id in cluster_bookings:
        if job_id in jobs_not_running or job_id not in all_jobs_squeue:
            delete_booking_call.append(remove_booked_for_job_id(job_id))
    logger.debug(f"CLEAN_BOOKINGS: {cluster_bookings}, {jobs_not_running}, {all_jobs_squeue}")
    if not delete_booking_call:
        logger.debug("CLEAN_BOOKINGS: no need to clean")
        return
    await asyncio.gather(*delete_booking_call)


async def filter_cluster_update_licenses(licenses_to_update: List) -> List:
    """Get the licenses in the cluster to filter the cluster update response."""
    local_licenses = await get_all_product_features_from_cluster()

    filtered_licenses = []
    for license in licenses_to_update:
        if license["product_feature"] in local_licenses:
            filtered_licenses.append(license)
    return filtered_licenses


async def get_bookings_sum_per_cluster(product_feature: str) -> Dict[str, int]:
    """
    Get booking sum for a license's bookings in each cluster.
    """
    response = await backend_client.get("/lm/api/v1/booking/all")
    bookings = response.json()

    booking_sum: Dict[str, int] = {}

    for booking in bookings:
        cluster_name = booking["cluster_name"]
        if booking["product_feature"] == product_feature:
            booking_sum[cluster_name] = booking_sum.get(cluster_name, 0) + booking["booked"]

    return booking_sum


async def create_or_update_reservation(reservation_data):
    """
    Create the reservation if it doesn't exist, otherwise update it.
    If the reservation cannot be updated, delete it and create a new one.
    """
    reservation = await scontrol_show_reservation()

    if reservation:
        updated = await scontrol_update_reservation(reservation_data, "30:00")
        if not updated:
            deleted = await scontrol_delete_reservation()
            LicenseManagerReservationFailure.require_condition(
                deleted, "Could not update or delete reservation."
            )
    else:
        created = await scontrol_create_reservation(reservation_data, "30:00")
        LicenseManagerReservationFailure.require_condition(created, "Could not create reservation.")


async def reconcile():
    """Generate the report and reconcile the license feature token usage."""
    logger.debug("Starting reconciliation")
    # Delete bookings for jobs that reached the grace time
    logger.debug("Cleaning bookings by grace time")
    await clean_booked_grace_time()
    logger.debug("Bookings cleaned by grace time")

    # Generate report and update the backend
    logger.debug("Reconciling licenses in the backend")
    await update_report()
    logger.debug("Backend licenses reconciliated")

    # Fetch from backend the licenses usage information
    logger.debug("Fetching licenses usage information from backend")
    response = await backend_client.get("/lm/api/v1/license/cluster_update")
    licenses_usage_info = response.json()
    logger.debug("Licenses usage information fetched from backend")

    # Filter the licenses to update
    licenses_to_update = await filter_cluster_update_licenses(licenses_usage_info)
    logger.debug(f"Licenses to update: {licenses_to_update}")

    reservation_data = []

    # Calculate how many licenses should be reserved for each license
    for license_data in licenses_to_update:
        # Get license usage from backend
        product_feature = license_data["product_feature"]
        product, feature = product_feature.split(".")
        server_used = license_data["license_used"]

        cluster_name = await get_cluster_name()

        bookings_per_cluster = await get_bookings_sum_per_cluster(product_feature)
        cluster_booking_sum = bookings_per_cluster.get(cluster_name, 0)
        other_cluster_booking_sum = sum(
            [booking for cluster, booking in bookings_per_cluster.items() if cluster != cluster_name]
        )

        # Get license configuration from backend
        config_id = await get_config_id_from_backend(product_feature)
        config = await backend_client.get(f"/lm/api/v1/config/{config_id}")
        config = config.json()

        license_server_type = config["license_server_type"]
        # Use feature name to get total and limit from feature data in the license config
        try:
            # Get total from new feature format
            total = config["features"][feature].get("total", 0)
            LicenseManagerFeatureConfigurationIncorrect.require_condition(
                total,
                f"The configuration for {feature} is incorrect. Please include the total amount of licenses.",
            )
        except AttributeError:
            # Fallback to get the total from the old feature format
            total = config["features"][feature]

        try:
            # Get limit from new feature format. If not specified, use the total as the limit
            limit = config["features"][feature].get("limit", total)
        except AttributeError:
            # Fallback to use the total as the limit for the old feature format
            limit = total

        # Get license usage from the cluster
        slurm_used = await get_tokens_for_license(f"{product_feature}@{license_server_type}", "Used")

        """
        The reserved amount represents how many licenses are already in use:
        Either in the license server or booked for a job (bookings from other cluster as well).
        If the license has a limit, the amount of licenses past the limit should be reserved too.

        The reservation is not meant to be used by any user, it's a way to block usage of licenses
        """

        reserved = (
            server_used - (slurm_used - cluster_booking_sum) + other_cluster_booking_sum + (total - limit)
        )

        if reserved < 0:
            reserved = 0

        if reserved > total:
            reserved = total

        if reserved:
            reservation_data.append(f"{product_feature}@{license_server_type}:{reserved}")

    # Create the reservation or update the existing one
    logger.debug(f"Reservation data: {reservation_data}")
    await create_or_update_reservation(",".join(reservation_data))

    logger.debug("Reconciliation done")


async def update_report():
    logger.info("Beginning forced reconciliation process")
    rep = await report()
    if not rep:
        logger.error(
            "No license data could be collected, check that tools are installed "
            "correctly and the right hosts/ports are configured in settings"
        )
        raise LicenseManagerEmptyReportError("Got an empty response from the license server")
    client = backend_client
    try:
        r = await client.patch(RECONCILE_URL_PATH, json=rep)
    except ConnectError as e:
        logger.error(f"{client.base_url}{RECONCILE_URL_PATH}: {e}")
        raise LicenseManagerBackendConnectionError("Failed to connect to the backend")

    if r.status_code != 200:
        logger.error(f"{r.url}: {r.status_code}!: {r.text}")
        raise LicenseManagerBackendConnectionError(f"Unexpected status code from report: {r.status_code}")

    logger.info(f"Forced reconciliation succeeded. backend updated: {len(rep)} feature(s)")
