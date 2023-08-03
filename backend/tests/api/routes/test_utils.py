from pytest import mark

from lm_backend.api.routes.utils import find_feature_id_by_name_and_client_id
from lm_backend.database import engine_factory


@mark.asyncio
async def test_find_feature_by_name_and_client_id__success(
    create_one_configuration,
    create_one_product,
    create_one_feature,
):
    session = engine_factory.get_session()
    feature_name = create_one_feature[0].name
    client_id = create_one_configuration[0].cluster_client_id

    feature_id = await find_feature_id_by_name_and_client_id(session, feature_name, client_id)

    assert feature_id == create_one_feature[0].id


@mark.asyncio
async def test_find_feature_by_name_and_client_id__fail(
    create_one_configuration,
    create_one_product,
    create_one_feature,
):
    session = engine_factory.get_session()
    feature_name = "not-a-feature"
    client_id = create_one_configuration[0].cluster_client_id

    feature_id = await find_feature_id_by_name_and_client_id(session, feature_name, client_id)

    assert feature_id == None
