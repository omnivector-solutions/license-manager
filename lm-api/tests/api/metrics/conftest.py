from pytest import fixture

from lm_api.api.models.configuration import Configuration
from lm_api.api.models.feature import Feature
from lm_api.api.models.product import Product
from lm_api.metrics import MetricsCollector


@fixture
async def metrics_data(sync_insert_objects):
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

    inserted_configurations = sync_insert_objects(
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

    inserted_products = sync_insert_objects(
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

    inserted_features = sync_insert_objects(features_to_add, Feature)

    return {
        "configurations": inserted_configurations,
        "products": inserted_products,
        "features": inserted_features,
    }


@fixture
def metrics_collector():
    return MetricsCollector()
