from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from lm_api.api.cruds.configuration import ConfigurationCRUD
from lm_api.api.cruds.feature import FeatureCRUD
from lm_api.api.cruds.generic import GenericCRUD
from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.license_server import LicenseServer
from lm_api.api.models.product import Product
from lm_api.api.schemas.configuration import (
    ConfigurationCompleteCreateSchema,
    ConfigurationCompleteUpdateSchema,
    ConfigurationCreateSchema,
    ConfigurationSchema,
    ConfigurationUpdateSchema,
)
from lm_api.api.schemas.feature import FeatureCreateSchema, FeatureUpdateSchema
from lm_api.api.schemas.license_server import LicenseServerCreateSchema, LicenseServerUpdateSchema
from lm_api.database import SecureSession, secure_session
from lm_api.permissions import Permissions

router = APIRouter()


crud_configuration = ConfigurationCRUD(Configuration)
crud_product = GenericCRUD(Product)
crud_feature = FeatureCRUD(Feature)
crud_license_server = GenericCRUD(LicenseServer)


@router.post(
    "",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_configuration(
    configuration: ConfigurationCompleteCreateSchema = Body(..., description="Configuration to be created"),
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.CONFIG_CREATE)),
):
    """
    Create a new configuration.

    The features for the configuration will be specified in the request body.
    If the feature's product doesn't exist, it will be created.
    """
    configuration_created = await crud_configuration.create(
        db_session=secure_session.session,
        obj=ConfigurationCreateSchema(**configuration.dict(exclude={"features", "license_servers"})),
    )

    if configuration.features:
        try:
            for feature in configuration.features:
                feature_obj = {
                    "name": feature.name,
                    "product_id": feature.product_id,
                    "config_id": configuration_created.id,
                    "reserved": feature.reserved,
                }
                await crud_feature.create(
                    db_session=secure_session.session, obj=FeatureCreateSchema(**feature_obj)
                )
        except HTTPException:
            await crud_configuration.delete(db_session=secure_session.session, id=configuration_created.id)
            raise

    if configuration.license_servers:
        try:
            for license_server in configuration.license_servers:
                license_server_obj = {
                    "config_id": configuration_created.id,
                    "host": license_server.host,
                    "port": license_server.port,
                }
                await crud_license_server.create(
                    db_session=secure_session.session, obj=LicenseServerCreateSchema(**license_server_obj)
                )
        except HTTPException:
            await crud_configuration.delete(db_session=secure_session.session, id=configuration_created.id)
            raise

    return await crud_configuration.read(
        db_session=secure_session.session, id=configuration_created.id, force_refresh=True
    )


@router.get(
    "",
    response_model=List[ConfigurationSchema],
    status_code=status.HTTP_200_OK,
)
async def read_all_configurations(
    search: Optional[str] = Query(None),
    sort_field: Optional[str] = Query(None),
    sort_ascending: bool = Query(True),
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.CONFIG_READ, commit=False)
    ),
):
    """Return all configurations with the associated license servers and features."""
    return await crud_configuration.read_all(
        db_session=secure_session.session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
    )


@router.get(
    "/by_client_id",
    response_model=List[ConfigurationSchema],
    status_code=status.HTTP_200_OK,
)
async def read_configurations_by_client_id(
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.CONFIG_READ, commit=False)
    ),
):
    """Return the configurations with the specified client_id."""
    client_id = secure_session.identity_payload.client_id

    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=("Couldn't find a valid client_id in the access token."),
        )

    return await crud_configuration.filter(
        db_session=secure_session.session, filter_expressions=[Configuration.cluster_client_id == client_id]
    )


@router.get(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
)
async def read_configuration(
    configuration_id: int,
    secure_session: SecureSession = Depends(
        secure_session(Permissions.ADMIN, Permissions.CONFIG_READ, commit=False)
    ),
):
    """Return a configuration with the associated license severs and features with a given id."""
    return await crud_configuration.read(
        db_session=secure_session.session, id=configuration_id, force_refresh=True
    )


@router.put(
    "/{configuration_id}",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_200_OK,
)
async def update_configuration(
    configuration_id: int,
    configuration_update: ConfigurationCompleteUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.CONFIG_UPDATE)),
):
    """
    Update a configuration in the database.

    If there are features in the payload, they'll be updated if they have an id,
    or they will be created if the id is None.

    If there are license servers in the payload, they'll updated if they have an id,
    or they will be created if the id is None.

    All resources related to the configuration that aren't present in the payload
    will be deleted.
    """
    if configuration_update.features is not None:
        await crud_configuration.delete_features(
            db_session=secure_session.session,
            configuration_id=configuration_id,
            payload=configuration_update,
        )

        for feature_update in configuration_update.features:
            if feature_update.id:
                await crud_feature.update(
                    db_session=secure_session.session,
                    id=feature_update.id,
                    obj=FeatureUpdateSchema(**feature_update.dict(exclude={"id"})),
                )
            else:
                feature_obj = {
                    "name": feature_update.name,
                    "product_id": feature_update.product_id,
                    "config_id": configuration_id,
                    "reserved": feature_update.reserved,
                }
                await crud_feature.create(
                    db_session=secure_session.session, obj=FeatureCreateSchema(**feature_obj)
                )

    if configuration_update.license_servers is not None:
        await crud_configuration.delete_license_servers(
            db_session=secure_session.session,
            configuration_id=configuration_id,
            payload=configuration_update,
        )

        for license_server_update in configuration_update.license_servers:
            if license_server_update.id:
                await crud_license_server.update(
                    db_session=secure_session.session,
                    id=license_server_update.id,
                    obj=LicenseServerUpdateSchema(**license_server_update.dict(exclude={"id"})),
                )
            else:
                license_server_obj = {
                    "config_id": configuration_id,
                    "host": license_server_update.host,
                    "port": license_server_update.port,
                }
                await crud_license_server.create(
                    db_session=secure_session.session, obj=LicenseServerCreateSchema(**license_server_obj)
                )

    if any(value for _, value in configuration_update.dict(exclude={"features", "license_servers"}).items()):
        return await crud_configuration.update(
            db_session=secure_session.session,
            id=configuration_id,
            obj=ConfigurationUpdateSchema(
                **configuration_update.dict(exclude={"features", "license_servers"})
            ),
        )
    elif configuration_update.features or configuration_update.license_servers:
        return await crud_configuration.read(
            db_session=secure_session.session, id=configuration_id, force_refresh=True
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid field to update configuration.",
        )


@router.delete(
    "/{configuration_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_configuration(
    configuration_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.ADMIN, Permissions.CONFIG_DELETE)),
):
    """
    Delete a configuration from the database.

    This will also delete the features and license servers associated.
    """
    return await crud_configuration.delete(db_session=secure_session.session, id=configuration_id)
