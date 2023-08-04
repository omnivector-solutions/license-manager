#!/usr/bin/env python3
"""
Reconciliation functionality live here.
"""
import asyncio
from typing import Dict, List

from lm_agent.backend_utils.models import BookingSchema
from lm_agent.backend_utils.utils import (
    get_bookings_for_job_id,
    get_cluster_configs_from_backend,
    get_cluster_grace_times,
    get_cluster_jobs_from_backend,
    get_feature_bookings_sum,
    make_feature_update,
    remove_job_by_slurm_job_id,
)
from lm_agent.exceptions import LicenseManagerEmptyReportError, LicenseManagerReservationFailure
from lm_agent.license_report import report
from lm_agent.logs import logger
from lm_agent.server_interfaces.license_server_interface import LicenseReportItem
from lm_agent.workload_managers.slurm.cmd_utils import (
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


def get_greatest_grace_time_for_job(grace_times: Dict[int, int], job_bookings: List[BookingSchema]) -> int:
    """
    Find the greatest grace_time among the features booked by the given job_id.
    """
    greatest_booking_feature = max(
        job_bookings, default=None, key=lambda job_booking: grace_times[job_booking.feature_id]
    )
    if not greatest_booking_feature:
        return -1
    return grace_times[greatest_booking_feature.feature_id]


def get_running_jobs(squeue_result: List) -> List:
    return [j for j in squeue_result if j["state"] == "RUNNING"]


async def clean_jobs_by_grace_time():
    """
    Clean the jobs where running time is greater than the grace_time.
    """
    logger.debug("GRACE_TIME START")

    formatted_squeue_output = return_formatted_squeue_out()
    if not formatted_squeue_output:
        logger.debug("GRACE_TIME no squeue")
        await clean_jobs(None)
        logger.debug("GRACE_TIME cleaned bookings that are not in the queue")
        return

    squeue_result = squeue_parser(formatted_squeue_output)
    squeue_running_jobs = get_running_jobs(squeue_result)

    get_bookings_call = [get_bookings_for_job_id(job["job_id"]) for job in squeue_running_jobs]
    results = await asyncio.gather(*get_bookings_call)
    bookings_for_running_jobs = {job["job_id"]: result for job, result in zip(squeue_running_jobs, results)}

    grace_times = await get_cluster_grace_times()

    # get the grace_time for each job
    for job in squeue_running_jobs:
        slurm_job_id = job["job_id"]
        greatest_grace_time = get_greatest_grace_time_for_job(
            grace_times, bookings_for_running_jobs[slurm_job_id]
        )
        # if the running_time is greater than the greatest grace_time, delete the booking for it
        if job["run_time_in_seconds"] > greatest_grace_time and greatest_grace_time != -1:
            logger.debug(f"GRACE_TIME: {greatest_grace_time}, {slurm_job_id}")
            await remove_job_by_slurm_job_id(slurm_job_id)

    await clean_jobs(squeue_result)


async def clean_jobs(squeue_result):
    """Clean the jobs that aren't running along with its bookings."""
    logger.debug("CLEAN_JOBS: start")

    cluster_jobs = [job.slurm_job_id for job in await get_cluster_jobs_from_backend()]
    if squeue_result is None:
        squeue_result = []

    jobs_not_running = [str(job["job_id"]) for job in squeue_result if job["state"] != "RUNNING"]
    all_jobs_squeue = [str(job["job_id"]) for job in squeue_result]
    logger.debug("CLEAN_JOBS: after building lists")

    delete_job_call = []

    for slurm_job_id in cluster_jobs:
        if slurm_job_id in jobs_not_running or slurm_job_id not in all_jobs_squeue:
            delete_job_call.append(remove_job_by_slurm_job_id(slurm_job_id))

    if not delete_job_call:
        logger.debug("CLEAN_JOBS: no need to clean")
        return

    await asyncio.gather(*delete_job_call)


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

    # Get cluster data
    configurations = await get_cluster_configs_from_backend()

    # Delete bookings for jobs that reached the grace time
    logger.debug("Cleaning jobs by grace time")
    await clean_jobs_by_grace_time()
    logger.debug("Jobs cleaned by grace time")

    # Generate report and update the backend
    logger.debug("Reconciling licenses in the backend")
    license_usage_info = await update_features()
    logger.debug("Backend licenses reconciliated")

    reservation_data = []

    # Calculate how many licenses should be reserved for each license
    for license_data in license_usage_info:
        # Get license usage from license report
        product_feature = license_data.product_feature
        server_used = license_data.used
        total = license_data.total

        # Get booking information from backend
        booking_sum = await get_feature_bookings_sum(product_feature)

        # Get license server type and reserved from the configuration in the backend
        for configuration in configurations:
            for feature in configuration.features:
                if f"{feature.product.name}.{feature.name}" == product_feature:
                    license_server_type = configuration.type
                    reserved = feature.reserved

        # Get license usage from the cluster
        slurm_used = await get_tokens_for_license(f"{product_feature}@{license_server_type}", "Used")

        """
        The reserved amount represents how many licenses are already in use:
        Either in the license server or booked for a job (bookings from other cluster as well).
        If the license has a reserved value, it should be reserved too.

        The reservation is not meant to be used by any user, it's a way to block usage of licenses
        """

        reservation_amount = server_used - slurm_used + booking_sum + reserved

        if reservation_amount < 0:
            reservation_amount = 0

        if reservation_amount > total:
            reservation_amount = total

        if reservation_amount:
            reservation_data.append(f"{product_feature}@{license_server_type}:{reservation_amount}")

        if reservation_data:
            logger.debug(f"Reservation data: {reservation_data}")

            # Create the reservation or update the existing one
            await create_or_update_reservation(",".join(reservation_data))
        else:
            logger.debug("No reservation needed")

        logger.debug("Reconciliation done")


async def update_features() -> List[LicenseReportItem]:
    """Send the license data collected from the cluster to the backend."""
    license_report = await report()

    if not license_report:
        logger.error(
            "No license data could be collected, check that tools are installed "
            "correctly and the right hosts/ports are configured in settings"
        )
        raise LicenseManagerEmptyReportError("Got an empty response from the license server")

    for license in license_report:
        product, feature = license.product_feature.split(".")
        await make_feature_update(feature=feature, total=license.total, used=license.used)

    return license_report
