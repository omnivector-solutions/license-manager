#!/usr/bin/env python3
"""license_manager.lic_tools.flexlm.flexlm_check_checked_out_licenses"""
import os
import re
import subprocess
from datetime import date, datetime

from license_manager.logging import log


LMSTAT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'lmstat'
)


def get_checked_out_licenses(license_server,
                             license_port,
                             license_feature,
                             debug=False):
    """Introspect checked out licenses."""
    license_server_uri = f"{license_port}@{license_server}"

    # Command to fetch data from flexlm license server
    cmd = [
        LMSTAT_PATH,
        '-c',
        license_server_uri,
        '-f',
        license_feature
    ]
    if debug:
        log.debug(f"FlexLM command: {' '.join(cmd)}")

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Use timeout of communicate with lmstat to detect if license server
    # is down.
    try:
        std_out, std_err = proc.communicate(timeout=6)
    except subprocess.TimeoutExpired:
        log.warning(f"License server is not responding: {license_server_uri}.")
        return False

    # Decode bytes string and split lines
    flexlm_server_output = std_out.decode("utf-8").split("\n")

    # Check for available licenses
    r = re.compile('.*start*.*licenses')
    licenses = list(filter(r.match, flexlm_server_output))

    if licenses is False:
        log.info("No licenses have been checked out")
        return False
    else:
        checked_out_licenses = dict()

        for lm_license in licenses:
            job, start_time, tokens = lm_license.strip().split(',')

            job_data = job.split()
            user = job_data[0]
            compute_host = job_data[1]

            tokens = int(tokens.split()[0])

            start_time = start_time.strip()
            datetime_object = datetime.strptime(
                '{} '.format(date.today().year) + start_time[6:],
                '%Y %a %m/%d %H:%M'
            )
            start_time_epoch = datetime_object.timestamp()

            if user not in checked_out_licenses:
                checked_out_licenses[user] = dict()

            checked_out_licenses[user][compute_host] = dict()
            checked_out_licenses[user][compute_host]['tokens'] = tokens
            checked_out_licenses[user][compute_host]['start_time'] = \
                int(start_time_epoch)

        if debug:
            log.debug(
                f"License server: {license_server} "
                f"License port: {license_port} "
                f"License feature: {license_feature}"
            )
            for user_name, user_dict in checked_out_licenses.items():
                log.debug(
                    f"User: '{user_name}' is using the following licenses: "
                )
                for compute_host in user_dict:
                    log.debug(
                        f"Host name: {compute_host} "
                        f"Feature: {license_feature} "
                        f"Tokens: {user_dict[compute_host]['tokens']} "
                        f"Start time: {user_dict[compute_host]['start_time']}"
                    )
        return checked_out_licenses


if __name__ == "__main__":
    license_server_ = "licserv0011.scania.com"
    license_server_port_ = '24200'
    license_feature_ = 'abaqus'
    checked_licenses = get_checked_out_licenses(
        license_server_,
        license_server_port_,
        license_feature_,
        debug=True
    )
