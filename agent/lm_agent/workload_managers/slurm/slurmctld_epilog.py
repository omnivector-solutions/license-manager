#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.
"""
import asyncio
import sys

from lm_agent.logs import init_logging, logger
from lm_agent.reconciliation import reconcile
from lm_agent.workload_managers.slurm.common import get_job_context


async def epilog():
    # Initialize the logger
    init_logging("slurmctld-epilog")
    job_context = get_job_context()
    # force reconcile
    try:
        await reconcile(cluster_name=job_context["cluster_name"])
    except Exception as e:
        logger.error(f"Failed to call reconcile with {e}")
        sys.exit(1)


def main():
    asyncio.run(epilog())


if __name__ == "__main__":
    main()
