"""
Reconciliation functionality live here.
"""
from lm_agent.backend_utils.utils import (
    get_all_features_bookings_sum,
    get_cluster_configs_from_backend,
    get_cluster_jobs_from_backend,
)
from lm_agent.logs import logger
from lm_agent.services.license_report import update_features
from lm_agent.services.clean_jobs_and_bookings import clean_jobs_and_bookings
from lm_agent.workload_managers.slurm.cmd_utils import (
    get_all_features_cluster_values,
    return_formatted_squeue_out,
    squeue_parser,
)
from lm_agent.workload_managers.slurm.reservations import (
    create_or_update_reservation,
    scontrol_delete_reservation,
    scontrol_show_reservation,
)


async def reconcile():
    """Generate the report and reconcile the license feature token usage."""
    logger.debug("Starting reconciliation")

    # Generate report and update the backend
    logger.debug("Reconciling licenses in the backend")
    license_usage_info = await update_features()
    logger.debug("Backend licenses reconciliated")

    # Get cluster data
    configurations = await get_cluster_configs_from_backend()

    # Get cluster jobs
    jobs = await get_cluster_jobs_from_backend()

    # Get feature bookings sum
    all_features_bookings_sum = await get_all_features_bookings_sum()

    # Get license usage from the cluster
    all_features_cluster_value = await get_all_features_cluster_values()

    # Get squeue result from cluster
    squeue_output = squeue_parser(await return_formatted_squeue_out())

    # Clean jobs and bookings
    await clean_jobs_and_bookings(configurations, jobs, squeue_output, license_usage_info)

    reservation_data = []

    # Calculate how many licenses should be reserved for each license
    for license_data in license_usage_info:
        # Get license usage from license report
        product_feature = license_data.product_feature
        report_used = license_data.used
        report_total = license_data.total

        # Get booking information from backend
        booking_sum = all_features_bookings_sum[product_feature]

        # Get license server type and reserved from the configuration in the backend
        for configuration in configurations:
            for feature in configuration.features:
                if f"{feature.product.name}.{feature.name}" == product_feature:
                    license_server_type = configuration.type.value

        # Get license usage from the cluster
        slurm_used = all_features_cluster_value[product_feature]["used"]
        slurm_total = all_features_cluster_value[product_feature]["total"]

        """
        The reserved amount represents how many licenses are already in use:
        Either in the license server or booked for a job (bookings from other cluster as well).

        If the license has a reserved value (licenses exclusive for usage in desktop environments),
        the value will be decreased from the Slurm counter and will be checked at booking creation
        time. This implies that the value won't need to be added to the reservation.

        The reservation is not meant to be used by any user, it's a way to block usage of licenses.

        If the report total is 0, it means that the license is not available in the license server
        and it should be fully reserved to prevent jobs from running and crashing.
        """

        if report_total == 0:
            reservation_amount = slurm_total
        else:
            reservation_amount = report_used - slurm_used + booking_sum

        if reservation_amount < 0:
            reservation_amount = 0

        if reservation_amount > slurm_total:
            reservation_amount = slurm_total

        if reservation_amount:
            reservation_data.append(f"{product_feature}@{license_server_type}:{reservation_amount}")

    if reservation_data:
        logger.debug(f"Reservation data: {reservation_data}")

        # Create the reservation or update the existing one
        await create_or_update_reservation(",".join(reservation_data))
    else:
        logger.debug("No reservation needed")

        existing_reservation = await scontrol_show_reservation()
        if existing_reservation:
            logger.debug("Deleting existing reservation")
            await scontrol_delete_reservation()

    logger.debug("Reconciliation done")
