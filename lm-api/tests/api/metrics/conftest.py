from pytest import fixture

from lm_api.api.metrics.collector import collect_feature_metrics
from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.product import Product
from lm_api.api.schemas.metrics import LICENSE_TOTAL, LICENSE_USED


@fixture
async def metrics_data(insert_objects):
    configurations_to_add = [
        {
            "name": "Abaqus",
            "cluster_client_id": "dummy1",
            "grace_time": 60,
            "type": "flexlm",
        },
        {
            "name": "Converge",
            "cluster_client_id": "dummy2",
            "grace_time": 60,
            "type": "rlm",
        },
    ]

    inserted_configurations = await insert_objects(
        configurations_to_add,
        Configuration,
    )

    products_to_add = [
        {
            "name": "abaqus",
        },
        {
            "name": "converge",
        },
    ]

    inserted_products = await insert_objects(
        products_to_add,
        Product,
    )

    features_to_add = [
        {
            "name": "abaqus",
            "product_id": inserted_products[0].id,
            "config_id": inserted_configurations[0].id,
            "reserved": 0,
            "total": 1000,
            "used": 25,
        },
        {
            "name": "converge_super",
            "product_id": inserted_products[1].id,
            "config_id": inserted_configurations[1].id,
            "reserved": 0,
            "total": 1000,
            "used": 250,
        },
    ]

    inserted_features = await insert_objects(features_to_add, Feature)

    return {
        "configurations": inserted_configurations,
        "products": inserted_products,
        "features": inserted_features,
    }


@fixture
async def setup_metrics_cache(synth_session, metrics_data):
    rows = await collect_feature_metrics(synth_session)

    LICENSE_TOTAL.clear()
    LICENSE_USED.clear()

    for r in rows:
        labels = {
            "cluster": r.cluster,
            "product": r.product,
            "feature": r.feature,
        }
        LICENSE_TOTAL.labels(**labels).set(r.total)
        LICENSE_USED.labels(**labels).set(r.used)

    return rows


@fixture(autouse=True)
def clear_metrics():
    LICENSE_TOTAL.clear()
    LICENSE_USED.clear()
    yield
    LICENSE_TOTAL.clear()
    LICENSE_USED.clear()
