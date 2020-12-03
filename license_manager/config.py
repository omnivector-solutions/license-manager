#!/usr/bin/env python3
"""license_manager.config."""
import os
import sys

import yaml


conf = None


class Config:
    """License manager config object."""

    def __init__(self, config_file):
        """Initialize slurm command paths."""
        bin_dir = "/usr/bin"

        if self._is_snap:
            bin_dir = "/snap/bin"

        self.SCONTROL_PATH = f"{bin_dir}/scontrol"
        self.SQUEUE_PATH = f"{bin_dir}/squeue"
        self.SACCT_PATH = f"{bin_dir}/sacct"

        try:
            # Load the yaml or log and exit.
            self._server_config = yaml.full_load(config_file.read_text())
        except yaml.YAMLError as e:
            print(f"Yaml formatting error - {e}")
            sys.exit(1)

    @property
    def _is_snap(self):
        return os.environ.get('SNAP')

    @property
    def server_config(self) -> dict:
        """Return the server.yaml."""
        return self._server_config


def init_config(config_file):
    """Create the config object and set the global."""
    global conf

    conf = Config(config_file)
    return conf


config = conf
