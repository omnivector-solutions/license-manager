#!/usr/bin/env python3
"""license_manager.lic_tools.flexlm.check_feature"""
import os
import re
import subprocess

from license_manager.logging import log


LMSTAT_PATH = os.path.join(os.path.dirname(__file__), "lmstat")


def check_feature(license_server, license_port, license_feature, debug=False):
    """Check license server for feature."""
    license_server_uri = f"{license_port}@{license_server}"

    cmd = [LMSTAT_PATH, "-c", license_server_uri, "-f", license_feature]

    log.info(" ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Use timeout of communicate with lmstat to detect if license server
    # is down.
    try:
        std_out, std_err = proc.communicate(timeout=6)
    except Exception as e:
        # subprocess.TimeoutExpired:
        log.warning(f"License server is not responding: {license_server_uri} - {e}")
        return False

    std_out = std_out.decode("utf-8").split("\n")

    # Check for communication error
    r = re.compile(".*Error getting status*")
    if list(filter(r.match, std_out)) is False:
        log.error("License server could not be reached")

    # Check for available licenses
    r = re.compile(".*Users of %s:*" % license_feature)
    licenses = list(filter(r.match, std_out))
    if licenses is False:
        log.error("License feature was not found on server")

    else:
        m = re.search("(\d{0,6} licenses issued)", licenses[0])
        if m:
            tokens_issued = m.group(0).split(" ")[0]
            if debug:
                log.debug(f"Issued: {tokens_issued}")
        else:
            log.error("License feature was not correctly read")
            return False

        m = re.search("(\d{0,6} licenses in use)", licenses[0])
        if m:
            tokens_used = m.group(0).split(" ")[0]
            if debug:
                log.debug(f"In use: {tokens_used}")
        else:
            log.error("License feature was not correctly read")
            return False

        return [int(tokens_issued), int(tokens_used)]
