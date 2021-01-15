#!/usr/bin/env python3
"""license_manager.config."""
import os
import sys

import yaml


class SlurmCmd:
    """Return slurm command paths.

    Supported commands:
        * SCONTROL
        * SQUEUE
        * SACCT
        * SACCTMGR

    Usage:
    slurm_cmd = SlurmCmd()

    subprocess.call([slurm_cmd.SQUEUE])
    """

    def __init__(self):
        """Determine if we are in a snap and set the path to the slurm cmds."""
        bin_dir = "/usr/bin"

        if os.environ.get("SNAP"):
            bin_dir = "/snap/bin"

        self.SCONTROL = f"{bin_dir}/scontrol"
        self.SQUEUE = f"{bin_dir}/squeue"
        self.SACCT = f"{bin_dir}/sacct"
        self.SACCTMGR = f"{bin_dir}/sacctmgr"


class Config:
    """License manager config object."""

    def __init__(self, config_file):
        """Initialize license-manager config."""
        try:
            # Load the yaml or log and exit.
            self._server_config = yaml.full_load(config_file.read_text())
        except yaml.YAMLError as e:
            print(f"Yaml formatting error - {e}")
            sys.exit(1)

    @property
    def server_config(self) -> dict:
        """Return the server.yaml."""
        return self._server_config


slurm_cmd = SlurmCmd()
