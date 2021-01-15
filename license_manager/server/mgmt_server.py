#!/usr/bin/env python3
"""license_manager.server.mgmt_server"""
import socketserver
import sys
import threading
import time

from license_manager.lic_tools import LicHandler
from license_manager.lic_tools.flexlm import (
    get_checked_out_licenses as flexlm_get_checked_out_licenses,
)
from license_manager.lic_tools.flexlm import check_feature as flexlm_check_feature
from license_manager.logging import log
from license_manager.server.handle_request import handle_request


# from systemd.daemon import notify


class ThreadedTCPRequestHandler(socketserver.StreamRequestHandler):
    """Threaded request handler."""

    def handle(self):
        """Handle the request."""
        # Get name of current thread
        cur_thread = threading.current_thread()

        try:
            # Receive data
            received_data = self.request.recv(1024)

            # Print received data
            with self.server.thread_lock:
                log.info(f"Thread received request: {cur_thread}")

            # Handle received data
            response = handle_request(
                received_data,
                self.server.kwargs["license_book"],
                self.server.thread_lock,
            )

            # Print response
            with self.server.thread_lock:
                log.info(f"Thread received response: {cur_thread}")

            # Response to client
            response = bytes(str(response), "ascii")
            self.request.sendall(response)

            # Print end message
            with self.server.thread_lock:
                log.info(f"Thread finished  request: {cur_thread}")

        except UnicodeDecodeError:
            response = bytes("ERROR - unknown characters received", "ascii")
            self.request.sendall(response)

        except Exception as e:
            log.error(f"Request handler: {cur_thread.name} - {e}")
            raise


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """ThreadedTCPServer."""

    def __init__(self, host_port_tuple, streamhandler, thread_lock, **kwargs):
        """Initialize ThreadedTCPServer."""
        super().__init__(host_port_tuple, streamhandler)
        self.thread_lock = thread_lock
        self.kwargs = kwargs


# Call back function to update available licenses and update slurmdbd regularly
def update_slurm_dbd(update_interval, license_book):
    """Update slurmdbd to be consistent with the license book."""
    try:
        # Get signal handle for exit of loop
        t = threading.currentThread()

        # Current thread name
        update_slurm_dbd_thread_name = threading.current_thread()

        while t.keep_running:
            time.sleep(update_interval)
            for feature in license_book:
                log.info(
                    f"{update_slurm_dbd_thread_name} - "
                    f"Update available licenses, feature: {feature}"
                )
                license_book[feature].__update_available_licenses__()
    except KeyboardInterrupt:
        log.error(
            "update_slurm_dbd - Interrupt from keyboard detected, " "shutting down."
        )
    finally:
        log.error("Callback update_slurm_dbd thread is down")


def mgmt_server(host="localhost", port=666, **kwargs):
    """Mgmt server."""
    # Licenses
    license_book = kwargs["license_book"]
    update_interval = kwargs["update_interval"]

    # Lock to allow for thread save data writing
    thread_lock = threading.Lock()

    # Instantiate server
    server = ThreadedTCPServer(
        (host, port), ThreadedTCPRequestHandler, thread_lock, **kwargs
    )

    # Initiate callback to keep Licenses updated

    update_callback_thread = threading.Thread(
        target=update_slurm_dbd, args=[update_interval, license_book]
    )
    update_callback_thread.keep_running = True
    update_callback_thread.start()

    with server:
        ip_, port_ = server.server_address

        log.info(f"Server started at: {ip_}:{port_}")

        # Start a thread with the server -- that thread will then start one
        # more thread for each request
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.start()

        log.info(f"Server loop running in thread: {server_thread.name}")
        # notify('READY=1')

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.debug("Interrupt from keyboard detected, shutting down.")
        finally:
            log.debug("Server is going down.....")
            # notify('STOPPING=1')

            # Shut down server
            server.shutdown()
            log.debug("State DOWN")
            log.debug(
                "Stop callback thread for license update, "
                f"may take up to {update_interval + 5}."
            )
            # Cancel update callbacks
            update_callback_thread.keep_running = False
            update_callback_thread.join(timeout=update_interval + 5)
            log.debug("State DOWN")
            time.sleep(2)


def initiate_license_tracking(server_config):
    """Initiate license tracking."""
    license_feature_bookings = dict()
    thread_lock = threading.Lock()

    for license_feature in server_config:
        license_server_type = server_config[license_feature]["server_type"]
        license_server_port = server_config[license_feature]["port"]
        booking_timeout = server_config[license_feature]["delay"]
        license_server_address = server_config[license_feature]["servers"]

        slurm_dbd_license = server_config[license_feature]["slurm_dbd"]
        if slurm_dbd_license == "":
            slurm_dbd_license = False

        if license_server_type == "flexlm":
            check_feature_function = flexlm_check_feature
            check_checked_out_license = flexlm_get_checked_out_licenses
        else:
            log.error(
                "License server configuration contains an unknown "
                f"license server type: {license_server_type}."
            )
            sys.exit(1)

        license_feature_bookings[license_feature] = LicHandler(
            license_feature,
            check_feature_function,
            check_checked_out_license,
            license_server_address,
            license_server_port,
            slurm_dbd_license,
            thread_lock,
            booking_timeout=booking_timeout,
        )
    return license_feature_bookings
