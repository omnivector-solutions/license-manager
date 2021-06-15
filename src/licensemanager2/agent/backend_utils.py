"""
Provide utilities that communicate with the backend.
"""
import yaml
from pathlib import Path
from typing import List, Any

from httpx import ConnectError
from licensemanager2.agent.settings import SETTINGS
from licensemanager2.agent.forward import async_client
from licensemanager2.agent import log as logger
from licensemanager2.backend.configuration import ConfigurationRow


GET_CONFIG_URL_PATH = "/api/v1/config/all"


async def get_config_from_backend():
    """
    Retrieves the config from the backend.

    """
    client = async_client()
    path = GET_CONFIG_URL_PATH

    try:
        resp = await async_client().get(path)
    except ConnectError as e:
        logger.error(f"{client.base_url}{path}: {e}")
        return []

    return [ConfigurationRow.parse_obj(x) for x in resp.json()]


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