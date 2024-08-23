"""
Service to clean jobs and bookings that are no longer needed.
"""
import asyncio
from collections import defaultdict
from typing import List, Dict, Tuple

from lm_agent.models import JobSchema, BookingSchema, ConfigurationSchema, LicenseReportItem
from lm_agent.backend_utils.utils import (
    remove_booking,
    remove_job_by_slurm_job_id,
)
from lm_agent.logs import logger
from lm_agent.models import ExtractedBookingSchema, ExtractedUsageSchema


def get_cluster_grace_times(cluster_configurations: List[ConfigurationSchema]) -> Dict[int, int]:
    """
    Get the grace time for each feature_id in the cluster.
    """
    grace_times = {
        feature.id: configuration.grace_time
        for configuration in cluster_configurations
        for feature in configuration.features
    }

    return grace_times


def get_greatest_grace_time_for_job(grace_times: Dict[int, int], job_bookings: List[BookingSchema]) -> int:
    """
    Find the greatest grace time among the features booked by the given job_id.

    If the job has more than one booking, only the greatest grace time will be returned.
    """
    grace_times_for_bookings = (grace_times[booking.feature_id] for booking in job_bookings)

    greatest_grace_time = max(grace_times_for_bookings)

    return greatest_grace_time


def extract_bookings_from_job(job: JobSchema) -> List[ExtractedBookingSchema]:
    """
    Extract all the bookings information from a job.
    """
    return [
        ExtractedBookingSchema(
            booking_id=booking.id,
            job_id=job.id,
            slurm_job_id=job.slurm_job_id,
            username=job.username,
            lead_host=job.lead_host,
            feature_id=booking.feature_id,
            quantity=booking.quantity,
        )
        for booking in job.bookings
    ]


def extract_usages_from_report(report_item: LicenseReportItem) -> List[ExtractedUsageSchema]:
    """
    Extract all the the usage information from a feature report

    Note that the lead_host from the license server comes with the full domain,
    but the lead_host from the job comes without the domain. This is why the
    lead_host is split by the dot and only the first part is used.
    """
    return [
        ExtractedUsageSchema(
            feature_id=report_item.feature_id,
            username=usage.username,
            lead_host=usage.lead_host.split(".")[0],
            quantity=usage.booked,
        )
        for usage in report_item.uses
    ]


def get_bookings_mapping(
    cluster_jobs: List[JobSchema],
) -> Dict[Tuple[int, str, str, int], List[ExtractedBookingSchema]]:
    """
    Map the bookings by creating a key with the required information for the matching.
    """
    bookings_mapping = defaultdict(list)

    for job in cluster_jobs:
        extracted_bookings = extract_bookings_from_job(job)

        for booking in extracted_bookings:
            key = (booking.feature_id, booking.username, booking.lead_host, booking.quantity)
            bookings_mapping[key].append(booking)

    return bookings_mapping


def get_usages_mapping(
    license_report: List[LicenseReportItem],
) -> Dict[Tuple[int, str, str, int], List[ExtractedUsageSchema]]:
    """
    Map the usages by creating a key with the required information for the matching.
    """
    usages_mapping = defaultdict(list)

    for report_item in license_report:
        extracted_usages = extract_usages_from_report(report_item)

        for usage in extracted_usages:
            key = (usage.feature_id, usage.username, usage.lead_host, usage.quantity)
            usages_mapping[key].append(usage)

    return usages_mapping


async def clean_jobs_without_bookings(cluster_jobs: List[JobSchema]) -> List[JobSchema]:
    """
    Clean the jobs that don't have any bookings.
    """
    logger.debug("##### Cleaning jobs without bookings")

    jobs_to_delete = []

    for job in cluster_jobs[:]:
        if not job.bookings:
            jobs_to_delete.append(job.slurm_job_id)
            cluster_jobs.remove(job)

    if not jobs_to_delete:
        logger.debug("##### No jobs without bookings to clean")
        return cluster_jobs

    await asyncio.gather(*[remove_job_by_slurm_job_id(job_id) for job_id in jobs_to_delete])

    logger.debug(f"##### Jobs cleaned: {jobs_to_delete}")
    logger.debug("##### Cleaned jobs without bookings")
    return cluster_jobs


async def clean_jobs_no_longer_running(
    cluster_jobs: List[JobSchema], squeue_result: List[Dict]
) -> List[JobSchema]:
    """
    Clean the jobs that aren't running along with its bookings.
    """
    logger.debug("##### Cleaning jobs that are no longer running")

    jobs_not_running = [str(job["job_id"]) for job in squeue_result if job["state"] != "RUNNING"]
    all_jobs_squeue = [str(job["job_id"]) for job in squeue_result]

    jobs_to_delete = []

    for job in cluster_jobs[:]:
        slurm_job_id = job.slurm_job_id
        if slurm_job_id in jobs_not_running or slurm_job_id not in all_jobs_squeue:
            jobs_to_delete.append(slurm_job_id)
            cluster_jobs.remove(job)

    if not jobs_to_delete:
        logger.debug("##### No need to clean jobs that are no longer running")
        return cluster_jobs

    await asyncio.gather(*[remove_job_by_slurm_job_id(job_id) for job_id in jobs_to_delete])

    logger.debug(f"##### Jobs cleaned: {jobs_to_delete}")
    logger.debug("##### Cleaned jobs that are no longer running")
    return cluster_jobs


async def clean_jobs_by_grace_time(
    cluster_jobs: List[JobSchema], squeue_result: List[Dict], grace_times: Dict[int, int]
) -> List[JobSchema]:
    """
    Clean the jobs where running time is greater than the grace_time.

    If the job has more than one booking, it will be deleted once the
    running time is greater than the greatest grace_time for any of the bookings.
    """
    logger.debug("##### Cleaning jobs by grace time")

    running_jobs = {str(job["job_id"]): job for job in squeue_result if job["state"] == "RUNNING"}

    jobs_to_delete = []

    for job in cluster_jobs[:]:
        greatest_grace_time = get_greatest_grace_time_for_job(grace_times, job.bookings)

        slurm_job_id = job.slurm_job_id

        running_job = running_jobs.get(slurm_job_id)
        if running_job and running_job["run_time_in_seconds"] > greatest_grace_time:
            jobs_to_delete.append(slurm_job_id)
            cluster_jobs.remove(job)

    if not jobs_to_delete:
        logger.debug("##### No jobs to clean by grace time")
        return cluster_jobs

    await asyncio.gather(*[remove_job_by_slurm_job_id(job_id) for job_id in jobs_to_delete])

    logger.debug(f"##### Jobs cleaned: {jobs_to_delete}")
    logger.debug("##### Cleaned jobs by grace time")
    return cluster_jobs


async def clean_bookings_by_usage(cluster_jobs: List[JobSchema], license_report: List[LicenseReportItem]):
    """
    Delete bookings if they match with a usage line in the license report.

    The bookings and the usage lines are mapped by a unique key composed by:
    * feature_id
    * username
    * lead_host
    * quantity

    This will group all bookings and all usages with the same information.

    The bookings can be deleted if the number of usages with the key matches
    the number of bookings with the key.

    - If there are more than one booking matching with the same usage,
    there's no way of knowning which booking relates to the usage.
    In this case, the bookings should be deleted by the grace time clean up.

    - If there are more than one usage matching the same booking,
    the booking could relate to any of the usages.
    In this case, the booking should be deleted by the grace time clean up.

    If there's an equal amount of usages and bookings, all the bookings have
    checked out their licenses from the license server, which means the bookings
    can be safely deleted by this clean up.
    """
    logger.debug("##### Cleaning bookings by usage")

    bookings_mapping = get_bookings_mapping(cluster_jobs)
    usages_mapping = get_usages_mapping(license_report)

    bookings_to_delete = []

    for key, bookings in bookings_mapping.items():
        if len(usages_mapping.get(key, [])) == len(bookings):
            bookings_to_delete.extend([booking.booking_id for booking in bookings])

    if not bookings_to_delete:
        logger.debug("##### No bookings to clean by matching")
        return

    await asyncio.gather(*[remove_booking(booking_id) for booking_id in bookings_to_delete])
    logger.debug(f"##### Bookings cleaned: {bookings_to_delete}")
    logger.debug("##### Cleaned bookings by matching")


async def clean_jobs_and_bookings(
    cluster_configurations: List[ConfigurationSchema],
    cluster_jobs: List[JobSchema],
    squeue_result: List[Dict],
    license_report: List[LicenseReportItem],
):
    """
    Clean the jobs and bookings that are no longer needed.

    The jobs can be deleted by:
    * Deleting the jobs that don't have any bookings.
    * Deleting the jobs that are no longer running.
    * Deleting the jobs that are running longer than the grace time.

    The bookings can be deleted by:
    * Deleting the bookings that have checked out their licenses from the license server.
    """
    logger.debug("##### Start cleaning jobs and bookings")

    grace_times = get_cluster_grace_times(cluster_configurations)

    jobs_with_bookings = await clean_jobs_without_bookings(cluster_jobs)
    jobs_still_running = await clean_jobs_no_longer_running(jobs_with_bookings, squeue_result)
    jobs_within_grace_time = await clean_jobs_by_grace_time(jobs_still_running, squeue_result, grace_times)
    await clean_bookings_by_usage(jobs_within_grace_time, license_report)

    logger.debug("##### Finished cleaning jobs and bookings")
