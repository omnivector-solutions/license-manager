#!/usr/bin/env python3
"""license_manager.main"""
import logging
import sys

from argparse import ArgumentParser
from pathlib import Path

from license_manager.agent.handlers import (
    run_controller_prolog_or_epilog,
)
from license_manager.config import init_config
from license_manager.logging import init_logging


logger = logging.getLogger("license-manager-agent")
logger.setLevel(logging.DEBUG)


def _get_input_args(argv):
    """Create argument parser and return cli args."""
    parser = ArgumentParser(
        description="LICENSE_MANAGER_AGENT"
    )

    parser.add_argument(
        "-t",
        "--script-type",
        dest="script_type",
        required=True,
        type=str,
        choices=['prolog', 'epilog'],
        help="Script type; prolog or epilog."
    )

    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        required=True,
        type=Path,
        help="Configuration file path."
    )

    parser.add_argument(
        "-l",
        "--log-file",
        dest="log_file",
        required=False,
        type=Path,
        help="Log file path."
    )
    return parser.parse_args(argv)


def main(argv=sys.argv[1:]):
    """License manager main."""
    # Get input arguments
    args = _get_input_args(argv)

    # Init the logger and config
    config = init_config(args.config_file)
    init_logging(args.log_file)

    license_manager_server_endpoint = config.server_config.get(
        'license_manager_server_endpoint'
    )

    # Ensure the config file contains the things we need.
    if not license_manager_server_endpoint:
        logger.error(
            "Need 'license_manager_server_endpoint' in config."
        )
        sys.exit(1)

    # Run controller [ prolog | epilog ].
    run_controller_prolog_or_epilog(
        license_manager_server_endpoint,
        args.script_type,
    )


if __name__ == "__main__":
    main()
