#!/usr/bin/env python3
"""license_manager.server.slurm_tools.check_used_feature_tokens"""
import re
import subprocess

from license_manager.config import slurm_cmd
from license_manager.logging import log


def slurm_dbd_check_used_feature_tokens(feature, license_server):
    """Check uesd feature tokens in slurmdbd."""
    cmd = [
        slurm_cmd.SCONTROL,
        "show",
        f"lic={feature}@{license_server}"
    ]
    log.debug(" ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = proc.communicate()
    log.debug(f"STD OUT: {std_out}")
    log.debug(f"STD ERR: {std_err}")

    # Decode output
    std_out = std_out.decode("utf-8")
    std_err = std_err.decode("utf-8")

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            "Could not update number of available tokens for: "
            f"Feature: {feature}, Server: {license_server}, "
            f"Stdout:  {std_out}, Stderr: {std_err}"
        )
        return False

    # If feature is not found, an empty string is returned
    if not std_out:
        return False

    # Parse response
    try:
        total = re.search('Total=(\d{0,8})', std_out) # NOQA
        total = total.group(1)

        used = re.search('Used=(\d{0,8})', std_out) # NOQA
        used = used.group(1)

        free = re.search('Free=(\d{0,8})', std_out) # NOQA
        free = free.group(1)

        return int(total), int(used), int(free)

    except IndexError as e:
        log.error(f"Response could not be parsed - {std_out} - {e}")
        return False
