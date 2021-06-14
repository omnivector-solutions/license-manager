"""
License objects and routes
"""
from pydantic import BaseModel
from typing import List

from fastapi import APIRouter

from licensemanager2.backend.schema import config_table
from licensemanager2.backend.storage import database


router_config = APIRouter()


class ConfigurationRow(BaseModel):
    """
    A configuration row
    """
    id: int
    product: str
    features: List[str]
    license_servers: List[str]
    license_server_type: str
    grace_time: int

    class Config:
        orm_mode = True


@router_config.get("/all", response_model=List[ConfigurationRow])
async def get_all_configurations():
    """
    Query database for all configurations.
    """
    query = (
        config_table.select()
        .order_by(config_table.c.id)
    )
    fetched = await database.fetch_all(query)
    return [ConfigurationRow.parse_obj(x) for x in fetched]


@router_config.get("/{id}", response_model=List[ConfigurationRow])
async def get_configuration(id):
    """
    Query database for configuration based on a given product.
    """
    query = (
        config_table.select()
        .where(config_table.c.id == id)
        .order_by(config_table.c.product)
    )
    fetched = await database.fetch_all(query)
    return [ConfigurationRow.parse_obj(x) for x in fetched]