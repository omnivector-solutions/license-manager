"""
Provide utilities that communicate with the backend.
"""
from typing import List

from httpx import ConnectError
from pydantic import BaseModel, ValidationError

from app.forward import async_client
from app.logs import logger

GET_CONFIG_URL_PATH = "/api/v1/config/all"


class BackendConfigurationRow(BaseModel):
    """
    NOTE: This is a copy of the schema from the backend.
          If the schema changes upstream in a non-reverse-compatible
          way, this schema should cause errors in deserialization.
    """

    class Config:
        extra = "ignore"

    product: str
    features: List[str]
    license_servers: List[str]
    license_server_type: str
    grace_time: int


async def get_config_from_backend() -> List[BackendConfigurationRow]:
    client = async_client()
    path = GET_CONFIG_URL_PATH

    try:
        resp = await async_client().get(path)
    except ConnectError as e:
        logger.error(f"Connection failed to backend: {client.base_url}{path}: {e}")
        return []

    configs = []
    for (i, config_row) in enumerate(resp.json()):
        try:
            configs.append(BackendConfigurationRow.parse_obj(config_row))
        except ValidationError as err:
            logger.error(f"Could not validate config entry at row {i}: {str(err)}")
    return configs
