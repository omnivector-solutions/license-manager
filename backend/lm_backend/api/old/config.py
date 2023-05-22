from ast import literal_eval
from typing import Dict, List, Optional, Union

from armasec import TokenPayload
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from lm_backend.api_schemas import ConfigurationItem, ConfigurationRow
from lm_backend.compat import INTEGRITY_CHECK_EXCEPTIONS
from lm_backend.constants import LicenseServerType, Permissions
from lm_backend.security import guard
from lm_backend.storage import database, search_clause, sort_clause
from lm_backend.table_schemas import config_searchable_fields, config_sortable_fields, config_table

router = APIRouter()


@router.get(
    "/agent/all",
    response_model=List[ConfigurationItem],
)
async def get_all_configurations_by_client_id(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    token_payload: TokenPayload = Depends(guard.lockdown(Permissions.CONFIG_VIEW)),
):
    """
    Query database for all configurations filtering by client_id.
    """
    # client_id identifies the cluster where the agent is running
    client_id = token_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    query = config_table.select().where(config_table.c.client_id == client_id)

    if search is not None:
        query = query.where(search_clause(search, config_searchable_fields))
    if sort_field is not None:
        query = query.order_by(sort_clause(sort_field, config_sortable_fields, sort_ascending))
    fetched = await database.fetch_all(query)
    config_rows = [ConfigurationRow.parse_obj(x) for x in fetched]
    return [
        ConfigurationItem(**item.dict(exclude={"features"}), features=literal_eval(item.features))
        for item in config_rows
    ]


@router.get(
    "/all",
    response_model=List[ConfigurationItem],
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_VIEW))],
)
async def get_all_configurations(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
):
    """
    Query database for all configurations.
    """
    query = config_table.select()
    if search is not None:
        query = query.where(search_clause(search, config_searchable_fields))
    if sort_field is not None:
        query = query.order_by(sort_clause(sort_field, config_sortable_fields, sort_ascending))
    fetched = await database.fetch_all(query)
    config_rows = [ConfigurationRow.parse_obj(x) for x in fetched]
    return [
        ConfigurationItem(**item.dict(exclude={"features"}), features=literal_eval(item.features))
        for item in config_rows
    ]


@router.get(
    "/license_server_types",
    response_model=List[LicenseServerType],
)
async def get_license_server_types():
    """
    Query database for all configurations.
    """
    return [e for e in LicenseServerType]


@router.get(
    "/{config_id}",
    response_model=ConfigurationItem,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_VIEW))],
)
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
    config_row = ConfigurationRow.parse_obj(fetched)
    return ConfigurationItem(
        **config_row.dict(exclude={"features"}), features=literal_eval(config_row.features)
    )


async def get_config_id_for_product_features(product_feature: str) -> Union[int, None]:
    """Return the config id for the given product_feature."""
    product, _ = product_feature.split(".")
    query = config_table.select().where(config_table.c.product == product)
    fetched = await database.fetch_one(query)
    config_row = ConfigurationRow.parse_obj(fetched)
    return config_row.id


@router.get("/", response_model=int)
async def get_config_id(product_feature: str):
    """Given the product_feature return the config_id."""
    _id = await get_config_id_for_product_features(product_feature)
    return _id


@database.transaction()
@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
async def add_configuration(configuration: ConfigurationRow):
    """
    Add a configuration to the database for the first time.
    """
    query = config_table.insert().values(
        # It is necessary to exclude None so the database won't attempt to insert a null id
        **configuration.dict(exclude_none=True),
    )

    try:
        inserted_id = await database.execute(query)
    except INTEGRITY_CHECK_EXCEPTIONS as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(f"Couldn't create configuration. Error: {str(e)}"),
        )

    return dict(
        message=f"Configuration id {inserted_id} created.",
    )


@database.transaction()
@router.put(
    "/{config_id}",
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
async def update_configuration(
    config_id: int,
    product: Optional[str] = Body(None),
    features: Optional[str] = Body(None),
    license_servers: Optional[List[str]] = Body(None),
    license_server_type: Optional[LicenseServerType] = Body(None),
    grace_time: Optional[int] = Body(None),
    client_id: Optional[str] = Body(None),
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
    if client_id is not None:
        update_dict["client_id"] = client_id
    q_update = config_table.update().where(config_table.c.id == config_id).values(update_dict)

    async with database.transaction():
        try:
            await database.execute(q_update)
        except INTEGRITY_CHECK_EXCEPTIONS as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(f"Couldn't update configuration {config_id}. Error: {str(e)}"),
            )

    return dict(message=f"Configuration id {config_id} updated.")


@database.transaction()
@router.delete(
    "/{config_id}",
    dependencies=[Depends(guard.lockdown(Permissions.CONFIG_EDIT))],
)
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
                f"Couldn't find configuration id {config_id} to delete, it does not exist in the database."
            ),
        )
    q = config_table.delete().where(config_table.c.id == config_id)

    try:
        await database.execute(q)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(f"Couldn't delete configuration {config_id})."),
        )

    return dict(message=f"Configuration id {config_id} deleted.")
