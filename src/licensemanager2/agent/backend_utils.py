"""
Provide utilities that communicate with the backend.
"""
from typing import List

from httpx import ConnectError

from licensemanager2.agent import log as logger
from licensemanager2.agent.forward import async_client
from licensemanager2.backend.configuration import ConfigurationRow


GET_CONFIG_URL_PATH = "/api/v1/config/all"


async def get_config_from_backend() -> List[ConfigurationRow]:
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