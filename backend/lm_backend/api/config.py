from typing import Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException, status

from lm_backend.api_schemas import ConfigurationRow
from lm_backend.compat import INTEGRITY_CHECK_EXCEPTIONS
from lm_backend.storage import database
from lm_backend.table_schemas import config_table

router = APIRouter()


@router.get("/all", response_model=List[ConfigurationRow])
async def get_all_configurations():
    """
    Query database for all configurations.
    """
    query = config_table.select()
    fetched = await database.fetch_all(query)
    return [ConfigurationRow.parse_obj(x) for x in fetched]


@router.get("/{config_id}", response_model=ConfigurationRow)
async def get_configuration(config_id: int):
    """
    Get one configuration row based on a given id.
    """
    query = config_table.select().where(config_table.c.id == config_id)
    fetched = await database.fetch_one(query)
    if not fetched:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Couldn't get config {config_id}, " "that ID does not exist in the database"),
        )
    return ConfigurationRow.parse_obj(fetched)


@database.transaction()
@router.post("/")
async def add_configuration(configuration: ConfigurationRow):
    """
    Add a configuration to the database for the first time.
    """
    query = config_table.insert().values(**vars(configuration))
    try:
        await database.execute(query)
    except INTEGRITY_CHECK_EXCEPTIONS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Couldn't insert config {configuration.id}), it already exists."),
        )

    return dict(message=f"inserted {configuration.id}")


@database.transaction()
@router.put("/{config_id}")
async def update_configuration(
    config_id: int,
    product: Optional[str] = Body(None),
    features: Optional[List[str]] = Body(None),
    license_servers: Optional[List[str]] = Body(None),
    license_server_type: Optional[str] = Body(None),
    grace_time: Optional[int] = Body(None),
):
    """
    Update a configuration row in the database with all of the
    optional arguments provided.
    """
    update_dict: Dict = {"id": config_id}
    if product is not None:
        update_dict["product"] = product
    if features is not None:
        update_dict["features"] = features
    if license_servers is not None:
        update_dict["license_servers"] = license_servers
    if license_server_type is not None:
        update_dict["license_server_type"] = license_server_type
    if grace_time is not None:
        update_dict["grace_time"] = grace_time
    q_update = config_table.update().where(config_table.c.id == config_id).values(update_dict)
    async with database.transaction():
        try:
            await database.execute(q_update)
        except INTEGRITY_CHECK_EXCEPTIONS as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return dict(message=f"updated configuration id: {config_id}")


@database.transaction()
@router.delete("/{config_id}")
async def delete_configuration(config_id: int):
    """
    Delete a configuration from the database based on its id.
    """
    query = config_table.select().where(config_table.c.id == config_id)
    rows = await database.fetch_one(query)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Couldn't find config id: {config_id} to delete, "
                "it does not exist in the database."
            ),
        )
    q = config_table.delete().where(config_table.c.id == config_id)
    try:
        await database.execute(q)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(f"Couldn't delete config {config_id})"),
        )
    return dict(message=f"Deleted {config_id} from the configuration table.")
