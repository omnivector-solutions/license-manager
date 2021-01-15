#!/usr/bin/env python3
"""license_manager.lic_tools.lic_handler"""
from time import time

from license_manager.logging import log
from license_manager.slurm_tools import (
    is_slurm_job_running,
    slurm_dbd_check_used_feature_tokens,
    slurm_dbd_update_feature_tokens,
)


class LicHandler:
    """Class for handling of updates, accounting of a License resource."""

    def __init__(
        self,
        license_feature,
        check_feature_function,
        check_checked_out_licenses,
        license_server_address,
        license_server_port,
        slurm_dbd_license,
        thread_lock,
        booking_timeout=False,
        debug=False,
    ):
        """Set initial attribute values."""
        # Debug mode for output to stdout
        self.debug = debug

        # Lock for threaded use to avoid corrupt data
        self.thread_lock = thread_lock

        # Assign received values
        self.license_feature = license_feature
        self.license_server_address = license_server_address
        self.license_server_port = license_server_port
        self.update_license = check_feature_function
        self.check_checked_out_licenses = check_checked_out_licenses
        self.booking_timeout = booking_timeout * 1  # Assumes minutes
        self.slurm_dbd_license = slurm_dbd_license

        # Table of booked licenses
        self.booked_licenses = dict()
        # Number of currently booked licenses
        self.booked_no_licenses = 0

        # Number of licenses of feature available
        self.tokens_available = 0

        # Loop over license servers until a response is received.
        for license_server in self.license_server_address:
            # Check license server status
            server_response = self.update_license(
                license_server, self.license_server_port, self.license_feature
            )
            if server_response:
                break

        if server_response:
            self.tokens_issued, self.tokens_used = server_response
        else:
            log.warning(
                "License status could not be checked. "
                f"Server: {license_server_address}"
                f"Port: {license_server_port}"
                f"Feature: {license_feature}"
            )

    def __update_available_licenses__(self):
        """Update the available licenses."""
        # Loop over license servers until a response is received, not False
        log.debug("Updating available licenses")
        for license_server in self.license_server_address:
            log.debug(f"License server: {license_server}")
            # Check license server status
            server_response = self.update_license(
                license_server, self.license_server_port, self.license_feature
            )
            log.debug(f"Response from {license_server}: {server_response}")
            if server_response:
                break

        if server_response:
            # Update bookings
            self.__update_booked_licenses__()

            with self.thread_lock:
                # Licenses available at license server
                self.tokens_issued, self.tokens_used = server_response

                # Licenses booked by jobs
                self.booked_no_licenses = 0
                for job_no, job_item in self.booked_licenses.items():
                    # Sum number of booked licenses
                    self.booked_no_licenses += job_item["required_tokens"]

                if self.debug:
                    log.debug(
                        "Updated licenses for feature: "
                        f"{self.license_feature}. "
                        f"Issued: {self.tokens_issued}"
                        f"Used: {self.tokens_used}"
                        f"Booked: {self.booked_no_licenses}"
                    )
                # Compute number of available licenses
                self.tokens_available = (
                    self.tokens_issued - self.tokens_used - self.booked_no_licenses
                )

        else:
            log.warning(
                "License status could not be checked. "
                f"Server: {self.license_server_address}, "
                f"Port: {self.license_server_port}, "
                f"Feature: {self.license_feature}"
            )

            # Set no available tokens
            with self.thread_lock:
                self.tokens_available = 0

        # Update tokens available at SLURM_DBD
        if self.slurm_dbd_license:
            response = slurm_dbd_check_used_feature_tokens(
                self.license_feature, self.slurm_dbd_license
            )
            if response:
                slurm_total, slurm_used, slurm_free = response

                # Compute tokens used by others, such as Workstation and LSF
                used_by_others = self.tokens_used - slurm_used

                # Compute tokens available for slurm_dbd
                new_slurm_total = self.tokens_issued - used_by_others

                # Set number of tokens available at slurm_dbd
                slurm_dbd_update_feature_tokens(self.license_feature, new_slurm_total)
                log.info("License feature tokens updated.")
            else:
                log.info("No response from slurmdbd.")

    def __update_booked_licenses__(self):  # NOQA
        """Update the booked licenses."""
        # Loop over license servers until a response is received, not False
        for license_server in self.license_server_address:

            # Update license status
            server_response = self.check_checked_out_licenses(
                license_server,
                self.license_server_port,
                self.license_feature,
                debug=False,
            )
            if server_response:
                break

        # Assign array with jobs to remove from bookings when started at
        # the license server
        #
        jobs_to_remove_from_bookings = []

        for job_id, job_item in self.booked_licenses.items():

            compute_host = job_item["compute_host_name"]
            user_name = job_item["user_name"]
            start_time = job_item["time"]

            if self.debug:
                if user_name in server_response:
                    debug_resp = server_response[user_name]
                else:
                    debug_resp = f"No reservation found for user: {user_name}"
                log.debug(f"Update booked licenses - Response: {debug_resp}")

            # TODO: Name of controller for running job to allow for multiple
            # slurm clusters, Maybe not required?
            if not is_slurm_job_running(job_id, None):
                # If job has ended at slurm controller, remove from
                # reservations
                jobs_to_remove_from_bookings.append(job_id)

            elif (user_name in server_response) and (
                compute_host in server_response[user_name]
            ):
                # If job has checked out licenses, remove from reservations
                log.info(
                    "License have been checked out for booking. "
                    f"Feature: {self.license_feature}, JobId: {job_id}"
                )
                jobs_to_remove_from_bookings.append(job_id)

            elif start_time + self.booking_timeout < time():
                # If the booking time-out is reached, return booking
                log.info(
                    f"Booking expired: Feature: {self.license_feature},"
                    f"JobId: {job_id}, "
                    f"Booking expired, timeout = {self.booking_timeout}"
                )
                jobs_to_remove_from_bookings.append(job_id)
            else:
                pass

        # Remove jobs from bookings
        with self.thread_lock:
            for job_id in jobs_to_remove_from_bookings:
                if self.debug:
                    log.debug(
                        f"Removing jobId {job_id} from bookings "
                        f"for feature: {self.license_feature}"
                    )
                del self.booked_licenses[job_id]

    def book_license(self, job_id, user_name, compute_host_name, required_tokens):
        """Book a license."""
        # Ensure correct format
        required_tokens = int(required_tokens)

        # Check if sufficient licenses are available
        self.__update_available_licenses__()

        # Execute write operations
        with self.thread_lock:
            if required_tokens <= self.tokens_available:
                self.booked_licenses[job_id] = {}
                self.booked_licenses[job_id]["compute_host_name"] = compute_host_name
                self.booked_licenses[job_id]["time"] = time()
                self.booked_licenses[job_id]["required_tokens"] = required_tokens
                self.booked_licenses[job_id]["user_name"] = user_name

                log.info(
                    f"Booked tokens for job id: {job_id}. "
                    f"Feature: {self.license_feature} "
                    f"Tokens requested: {required_tokens} "
                    f"Tokens available: {self.tokens_available}"
                )
                booking_successful = True
            else:
                log.info(
                    f"Not enough tokens for job id {job_id}. "
                    f"Feature: {self.license_feature} "
                    f"Tokens requested: {required_tokens} "
                    f"Tokens available: {self.tokens_available}"
                )
                booking_successful = False

        return booking_successful

    def return_license(self, job_id, user_name, compute_host_name):
        """Return the license."""
        try:
            if job_id in self.booked_licenses:
                booked_licenses_hostname = self.booked_licenses[job_id][
                    "compute_host_name"
                ]
                if (booked_licenses_hostname == compute_host_name) and (
                    self.booked_licenses[job_id]["user_name"] == user_name
                ):

                    # Acquire thread lock and remove job_id
                    with self.thread_lock:
                        del self.booked_licenses[job_id]

                    # Update available licenses
                    self.__update_available_licenses__()
                    log.info(
                        f"Booking for feature '{self.license_feature}' "
                        f"and jobId {job_id} was returned"
                    )
                    return True
                else:
                    log.info(
                        f"Booking for feature '{self.license_feature}' and "
                        f"jobId {job_id} was found, but job attributes "
                        "mismatch."
                    )
                    return False
            else:
                log.info(
                    f"No booking for feature '{self.license_feature}' "
                    f"and jobId {job_id} was found."
                )
                return False
        except Exception as e:
            log.error(
                f"License was not returned - {e}, "
                f"Feature: {self.license_feature}, "
                f"JobId: {job_id}, "
                f"Username: {user_name}"
            )
            return False

    def available_tokens(self):
        """Return available tokens."""
        # Update status
        self.__update_available_licenses__()
        # Return result
        return self.tokens_available

    def booked_tokens(self):
        """Return booked tokens."""
        # Update status
        self.__update_available_licenses__()
        # Return result
        return self.booked_no_licenses

    def free_at_license_server(self):
        """Return free licenses at license server."""
        # Update status
        self.__update_available_licenses__()
        # Return result
        return self.tokens_issued - self.tokens_used
