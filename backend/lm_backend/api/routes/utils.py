from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from lm_backend.api.cruds.generic import GenericCRUD
from lm_backend.api.models.configuration import Configuration
from lm_backend.api.models.feature import Feature
from lm_backend.api.schemas.configuration import ConfigurationCreateSchema, ConfigurationUpdateSchema
from lm_backend.api.schemas.feature import FeatureCreateSchema, FeatureUpdateSchema

crud_feature = GenericCRUD(Feature, FeatureCreateSchema, FeatureUpdateSchema)
crud_configuration = GenericCRUD(Configuration, ConfigurationCreateSchema, ConfigurationUpdateSchema)


async def find_feature_id_by_name_and_client_id(db_session: AsyncSession, feature_name: str, client_id: str):
    """
    Find the feature id by name and client id.
    """
    features: List[Feature] = await crud_feature.filter(
        db_session=db_session, filter_expressions=[Feature.name == feature_name]
    )

    for feature in features:
        configuration = await crud_configuration.read(db_session=db_session, id=feature.config_id)

        if configuration and configuration.cluster_client_id == client_id:
            return feature.id
