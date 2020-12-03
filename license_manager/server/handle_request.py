#!/usr/bin/env python3
"""license_manager.server.handle_request"""
import json

from license_manager.logging import log


def handle_request(data, license_book, thread_lock): # NOQA
    """Parse and handle incoming request."""
    try:
        # Convert data to json format
        json_data = json.loads(data)
    except json.JSONDecodeError as e:
        log.error(f"Request could read properly - Expecting json format - {e}")
        return False

    # Collect status of all license requests
    status_of_requests = []

    # Handle requests
    for request in json_data:
        try:
            license_feature = request['feature']
            required_tokens = request['required_tokens']
            job_id = request['job_id']
            user_name = request['user_name']
            compute_host_name = request['compute_host_name']
            action = request['action']
        except KeyError as e:
            log.error(
                "The request is missing mandatory information: "
                f"key: {e}"
            )
            status_of_requests.append(False)
            break

        if license_feature not in license_book:
            log.debug(
                f"Requested feature '{license_feature}' is not handled "
                "by license manager"
            )
            status_of_requests.append(False)
            break

        try:
            if action == 'book_license':
                action_is_booking = True
                current_feature_status = \
                    license_book[license_feature].book_license(
                        job_id,
                        user_name,
                        compute_host_name,
                        required_tokens
                    )
            elif action == "return_license":
                action_is_booking = False
                current_feature_status = \
                    license_book[license_feature].return_license(
                        job_id,
                        user_name,
                        compute_host_name
                    )
            else:
                action_is_booking = False
                log.debug("Unknown action was requested {action}")
                current_feature_status = False

        except Exception as e:
            log.error(f"License request could not be handled - {e}")
            log.error(request)
            current_feature_status = False
            action_is_booking = False

        status_of_requests.append(current_feature_status)

    # Handle the one or more failed requests and return booking
    if action_is_booking and (False in status_of_requests):
        log.debug("All licenses could NOT be booked, return all bookings...")
        booking_response = False
        feature_status_zip = zip(status_of_requests, json_data)
        for current_feature_status, request in feature_status_zip:
            # If license was booked, return license
            if current_feature_status:
                license_feature = request['feature']
                job_id = request['job_id']
                user_name = request['user_name']
                compute_host_name = request['compute_host_name']
                log.info(f"Returning license - {license_feature}")
                current_feature_status = \
                    license_book[license_feature].return_license(
                        job_id,
                        user_name,
                        compute_host_name
                    )
    else:
        booking_response = True

    try:
        with thread_lock:
            if booking_response:
                if action == 'book_license':
                    log.info("Booking successful")
                elif action == 'return_license':
                    log.info("Booking return successful")
                else:
                    log.warning("Unexpected state")
            else:
                if action == 'book_license':
                    log.debug("Booking failed - Insufficient resources")
                elif action == 'return_license':
                    log.debug("No matching booking was found, expired?")
                else:
                    log.warning("Unexpected state")
        return booking_response
    except Exception as e:
        log.warning(f"Failed as data could not be interpreted - {e}")
        return False
