from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.models.license_server import LicenseServer
from lm_backend.api.models.product import Product
from lm_backend.api.schemas.configuration import (
    ConfigurationCompleteCreateSchema,
    ConfigurationCreateSchema,
    ConfigurationSchema,
    ConfigurationUpdateSchema,
)
from lm_backend.api.schemas.feature import FeatureCreateSchema, FeatureUpdateSchema
from lm_backend.api.schemas.license_server import LicenseServerCreateSchema, LicenseServerUpdateSchema
from lm_backend.api.schemas.product import ProductCreateSchema, ProductUpdateSchema
from lm_backend.database import SecureSession, secure_session
from lm_backend.permissions import Permissions

router = APIRouter()


crud_configuration = GenericCRUD(Configuration, ConfigurationCreateSchema, ConfigurationUpdateSchema)
crud_product = GenericCRUD(Product, ProductCreateSchema, ProductUpdateSchema)
crud_feature = GenericCRUD(Feature, FeatureCreateSchema, FeatureUpdateSchema)
crud_license_server = GenericCRUD(LicenseServer, LicenseServerCreateSchema, LicenseServerUpdateSchema)


@router.post(
    "",
    response_model=ConfigurationSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_configuration(
    configuration: ConfigurationCompleteCreateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """
    Create a new configuration.

    The features for the configuration will be specified in the request body.
    If the feature's product doesn't exist, it will be created.
    """
    configuration_created: Configuration = await crud_configuration.create(
        db_session=secure_session.session,
        obj=ConfigurationCreateSchema(**configuration.dict(exclude={"features", "license_servers"})),
    )

    if configuration.features:
        try:
            for feature in configuration.features:
                products: List[Product] = await crud_product.filter(
                    secure_session.session, [Product.name == feature.product_name]
                )
                if not products:
                    product_obj = {
                        "name": feature.product_name,
                    }
                    product_created: Product = await crud_product.create(
                        db_session=secure_session.session, obj=ProductCreateSchema(**product_obj)
                    )
                    product_id = product_created.id
                else:
                    product_id = products[0].id

                feature_obj = {
                    "name": feature.name,
                    "product_id": product_id,
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
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_VIEW)),
):
    """Return all configurations with the associated license servers and features."""
    return await crud_configuration.read_all(
        db_session=secure_session.session,
        search=search,
        sort_field=sort_field,
        sort_ascending=sort_ascending,
        force_refresh=True,
    )


@router.get(
    "/by_client_id",
    response_model=List[ConfigurationSchema],
    status_code=status.HTTP_200_OK,
)
async def read_configurations_by_client_id(
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_VIEW)),
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
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_VIEW)),
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
    configuration_update: ConfigurationUpdateSchema,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """Update a configuration in the database."""
    return await crud_configuration.update(
        db_session=secure_session.session,
        id=configuration_id,
        obj=configuration_update,
    )


@router.delete(
    "/{configuration_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_configuration(
    configuration_id: int,
    secure_session: SecureSession = Depends(secure_session(Permissions.CONFIG_EDIT)),
):
    """
    Delete a configuration from the database.

    This will also delete the features and license servers associated.
    """
    return await crud_configuration.delete(db_session=secure_session.session, id=configuration_id)
