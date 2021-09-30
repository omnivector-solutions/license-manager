#!/usr/bin/env python3
"""
The EpilogSlurmctld executable.
"""
import asyncio
import sys

from lm_agent.logs import init_logging, logger
from lm_agent.workload_managers.slurm.cmd_utils import reconcile


async def epilog():
    # Initialize the logger
    init_logging("slurmctld-epilog")
    # force reconcile
    try:
        await reconcile()
    except Exception as e:
        logger.error(f"Failed to call reconcile with {e}")
        sys.exit(1)


def main():
    asyncio.run(epilog())


if __name__ == "__main__":
    main()
