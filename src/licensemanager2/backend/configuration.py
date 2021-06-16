"""
License objects and routes
"""
from pydantic import BaseModel
from typing import List

from fastapi import APIRouter, HTTPException

from licensemanager2.backend.schema import config_table
from licensemanager2.backend.storage import database
from licensemanager2.common_api import OK
from licensemanager2.compat import INTEGRITY_CHECK_EXCEPTIONS


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


@database.transaction()
@router_config.post("/", response_model=OK)
async def add_configuration(configuration: ConfigurationRow):
    """
    Add a configuration to the database for the first time.
    """
    query = (
        config_table.insert()
        .values(**vars(configuration))
    )
    try:
        await database.execute(query)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't insert config {configuration.id}), it already exists.")
        )

    return OK(
        message=f"inserted {configuration.id}"
    )


@database.transaction()
@router_config.put("/{id}", response_model=OK)
async def update_configuration(configuration: ConfigurationRow, id: str):
    """
    Update a configuration to the database.
    """
    query = (
        config_table.update()
        .where(config_table.c.id == configuration.id)
        .values(**vars(configuration))
    )
    try:
        await database.execute(query)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't insert config {configuration.id})")
        )

    return OK(
        message=f"inserted {configuration.id}"
    )


@database.transaction()
@router_config.delete("/{id}", response_model=OK)
async def delete_configuration(id: str):
    """
    Delete a configuration from the database based on its id.
    """
    query = (
        config_table.select()
        .where(config_table.c.id == id)
        .order_by(config_table.c.id)
    )
    rows = await database.fetch_all(query)
    if not rows:
        raise HTTPException(
            status_code=400,
            detail=(f"Couldn't find config id: {id} to delete"),
        )

    q = config_table.delete().where(config_table.c.id == id)
    try:
        await database.execute(q)
    except Exception:
        raise HTTPException(
            status_code=409,
            detail=(f"Couldn't delete config {id})")
        )
    return OK(message=f"Deleted {id} from the configuration table.")