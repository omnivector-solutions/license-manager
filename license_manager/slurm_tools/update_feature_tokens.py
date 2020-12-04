#!/usr/bin/env python3
"""license_manager.server.slurm_tools.slurm_dbd_update_feature_tokens"""
import subprocess

from license_manager.config import slurm_cmd
from license_manager.logging import log


def slurm_dbd_update_feature_tokens(feature, tokens):
    """Update tokens for a feature."""
    cmd = [
        slurm_cmd.SACCTMGR,
        "modify",
        "resource",
        f"name={feature}",
        "set",
        f"count={tokens}",
        "-i"
    ]

    log.debug(" ".join(cmd))

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    std_out, std_err = proc.communicate()

    # Decode output
    std_out = std_out.decode("utf-8")
    std_err = std_err.decode("utf-8")

    log.debug(f"STDOUT : {std_out}")
    log.debug(f"STDERR : {std_err}")

    # Check that the process completed successfully for the requested job id
    if not proc.returncode == 0:
        log.error(
            "Could not update number of available tokens for: "
            f"Feature: {feature}, Tokens: {tokens}, "
            f"Stdout:  {std_out}, Stderr: {std_err}"
        )
        return False

    return True
