#!/usr/bin/env python3
"""
Reconciliation functionality live here.
"""
import asyncio
from typing import Dict, List

from httpx import ConnectError

from lm_agent.backend_utils import (
    backend_client,
    get_bookings_from_backend,
    get_config_from_backend,
    get_config_id_from_backend,
)
from lm_agent.exceptions import LicenseManagerBackendConnectionError, LicenseManagerEmptyReportError
from lm_agent.logs import logger
from lm_agent.tokenstat import report
from lm_agent.workload_managers.slurm.cmd_utils import (
    get_all_product_features_from_cluster,
    get_cluster_name,
    get_tokens_for_license,
    return_formatted_squeue_out,
    sacctmgr_modify_resource,
    squeue_parser,
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


async def reconcile():
    """Generate the report and reconcile the license feature token usage."""
    await clean_booked_grace_time()
    r = await update_report()
    response = await backend_client.get("/lm/api/v1/license/cluster_update")
    configs = await get_config_from_backend()
    licenses_to_update = response.json()

    # Filter licenses to reconcile only licenses in the cluster
    filtered_licenses = await filter_cluster_update_licenses(licenses_to_update)

    for license_data in filtered_licenses:
        product_feature = license_data["product_feature"]
        bookings_sum = license_data["bookings_sum"]
        license_total = license_data["license_total"]
        license_used = license_data["license_used"]
        config_id = await get_config_id_from_backend(product_feature)
        minimum_value = 0
        server_type = ""
        for config in configs:
            if config.id == config_id:
                minimum_value = config.features[product_feature.split(".")[1]]
                server_type = config.license_server_type
                break
        slurm_used = await get_tokens_for_license(product_feature + "@" + server_type, "Used")
        if slurm_used is None:
            slurm_used = 0
        new_quantity = license_total - license_used - bookings_sum + slurm_used
        if new_quantity > license_total:
            new_quantity = license_total
        if new_quantity < minimum_value:
            new_quantity = minimum_value
        product, feature = product_feature.split(".")
        update_resource = await sacctmgr_modify_resource(product, feature, new_quantity)
        if update_resource:
            logger.info("Slurmdbd updated successfully.")
        else:
            logger.info("Slurmdbd update unsuccessful.")
    return r


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
