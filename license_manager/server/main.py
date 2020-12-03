#!/usr/bin/env python3
"""license_manager main module."""
import os
import sys

from argparse import ArgumentParser
from pathlib import Path
from signal import SIGINT, signal, SIGTERM

from license_manager.config import init_config
from license_manager.logging import init_logging
from license_manager.server.mgmt_server import (
    initiate_license_tracking,
    mgmt_server,
)


def _get_shutdown_handler(message=None):
    """Build a shutdown handler, called from the signal methods.

    :param message:
        Message to display at shutdown. Defaults to none
    """
    def handler(signum, frame):
        # If we want to do anything on shutdown, such as stop motors on a
        # robot, you can add it here.
        try:
            print(f"Server Daemon: {message}")
            raise KeyboardInterrupt
        finally:
            print("Server Daemon has ended")
            sys.exit(0)
    return handler


def _get_input_args(argv):
    """Create argument parser and return cli args."""
    parser = ArgumentParser(
        description="LICENSE_MANAGER_SERVER"
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
    # Setup handlers to to shut down properly and behave as a service
    signal(SIGINT, _get_shutdown_handler(message='SIGINT received'))
    signal(SIGTERM, _get_shutdown_handler(message='SIGTERM received'))

    # Get input arguments
    args = _get_input_args(argv)

    # Initialize logging config global objects
    config = init_config(args.config_file)
    init_logging(args.log_file)

    pid_file = Path("/tmp/slurm_lic.pid")
    pid = f"{os.getpid()}\n\r"

    try:
        # Starting server
        print(f"Starting with parent PID: {pid}")
        pid_file.write_text(pid)

        # Read configuration and generate current structure
        license_feature_booking_instances = initiate_license_tracking(
            config.server_config,
        )

        # Start license management server
        mgmt_server(
            license_book=license_feature_booking_instances,
            update_interval=60,
            port=2048,
            host='0.0.0.0',
        )
    finally:
        # Clean up pid file
        if pid_file.exists():
            pid_file.unlink()


if __name__ == "__main__":
    main()
