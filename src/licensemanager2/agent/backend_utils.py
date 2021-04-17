"""
Provide utilities that communicate with the backend.
"""
import yaml
from pathlib import Path
from typing import List, Any
from licensemanager2.agent.settings import SETTINGS


def get_license_server_features() -> List[Any]:
    """Return the license_servers and features from the backend.

    This code makes a request to the backend and retrieves the license servers
    and associated features to reconcile/report.

    The return of this function should contain a list of license servers and features.

    [

        {
            "license_server_type": "flexlm",
            "features": [
                "abaqus",
            ]
        }
    ]


    """
    # TODO: Replace this code with code that pulls the license server config from the backend.
    license_server_config_file = SETTINGS.LICENSE_SERVER_FEATURES_CONFIG_PATH
    license_server_config = list()
    if license_server_config_file is not None:
        try:
            license_server_config = yaml.load(
                Path(license_server_config_file).read_text(),
                Loader=yaml.FullLoader
            )
        except yaml.YAMLError as e:
            # log.error(f"Cannot read {SETTINGS.LICENSE_SERVER_FEATURES_CONFIG_PATH} - {e}")
            print(e)
    return license_server_config
