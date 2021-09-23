#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.
"""
import asyncio
import sys

from lm_agent.backend_utils import get_config_from_backend
from lm_agent.logs import init_logging, logger
from lm_agent.workload_managers.slurm.cmd_utils import (
    get_required_licenses_for_job,
    get_tokens_for_license,
    sacctmgr_modify_resource,
)
from lm_agent.workload_managers.slurm.common import get_job_context


async def epilog():
    # Initialize the logger
    init_logging("slurmctld-epilog")
    # Acqure the job context and get the job_id.
    ctxt = get_job_context()
    job_id = ctxt["job_id"]

    try:
        required_licenses = await get_required_licenses_for_job(job_id)
    except Exception as e:
        logger.error(f"Failed to call get_required_licenses_for_job with {e}")
        sys.exit(1)

    if not required_licenses:
        logger.debug("No licenses required, exiting!")
        sys.exit(0)

    if len(required_licenses) > 0:
        # Create a list of tracked licenses in the form <product>.<feature>
        tracked_licenses = list()
        try:
            entries = await get_config_from_backend()
        except Exception as e:
            logger.error(f"Failed to call get_config_from_backend with {e}")
            sys.exit(1)
        for entry in entries:
            for feature in entry.features:
                tracked_licenses.append(f"{entry.product}.{feature}")

        # If a license booking's product feature is tracked,
        # update slurm's view of the token totals
        for license_booking in required_licenses:
            product_feature = license_booking.product_feature
            product, feature = product_feature.split(".")
            license_server_type = license_booking.license_server_type
            tokens_to_remove = license_booking.tokens
            license = f"{product_feature}@{license_server_type}"

            if product_feature in tracked_licenses:
                try:
                    total = await get_tokens_for_license(license, "Total")
                except Exception as e:
                    logger.error(f"Failed to call get_tokens_for_license with {e}")
                    sys.exit(1)
                update_resource = await sacctmgr_modify_resource(product, feature, total - tokens_to_remove)

                if update_resource:
                    logger.info("Slurmdbd updated successfully.")
                else:
                    logger.info("Slurmdbd update unsuccessful.")

    sys.exit(0)


def main():
    asyncio.run(epilog())


if __name__ == "__main__":
    main()
