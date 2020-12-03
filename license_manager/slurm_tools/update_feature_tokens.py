#!/usr/bin/env python3
"""license_manager.server.slurm_tools.slurm_dbd_update_feature_tokens"""
import subprocess

from license_manager.config import config
from license_manager.logging import log


def slurm_dbd_update_feature_tokens(feature, tokens):
    """Update tokens for a feature."""
    cmd = [
        config.SACCTMGR_PATH,
        "modify",
        "resource",
        f"name={feature}"
        "set",
        f"count={tokens}",
        "-i"
    ]

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = proc.communicate()

    # Decode output
    std_out = std_out.decode("utf-8")
    std_err = std_err.decode("utf-8")

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            "Could not update number of available tokens for: "
            f"Feature: {feature}, Server: {feature}, "
            f"Stdout:  {std_out}, Stderr: {tokens}"
        )
        return False

    return True
