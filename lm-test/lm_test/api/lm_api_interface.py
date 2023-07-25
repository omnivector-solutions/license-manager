from lm_test.config import settings
from lm_test.utils import LM_API_Client, create_resource, delete_resource


lm_api_client = LM_API_Client()


async def setup():
    """
    Set up the License Manager API with the resouces needed for the integration test.
    """
    print("Setting up License Manager API...")

    cluster_id = settings.CLUSTER_ID

    configuration_data = {
        "name": "test-configuration",
        "cluster_id": cluster_id,
        "grace_time": 60,
        "type": "flexlm",
    }
    configuration_id = (await create_resource(lm_api_client, configuration_data, "/lm/configurations/"))["id"]
    print(f"Created configuration with id: {configuration_id}")

    license_server_data = {
        "config_id": configuration_id,
        "host": "test-host",
        "port": 27000,
    }
    license_server_id = (await create_resource(lm_api_client, license_server_data, "/lm/license_servers/"))["id"]
    print(f"Created license server with id: {license_server_id}")

    product_data = {
        "name": "test_product",
    }
    product_id = (await create_resource(lm_api_client, product_data, "/lm/products/"))["id"]
    print(f"Created product with id: {product_id}")

    feature_data = {
        "name": "test_feature",
        "product_id": product_id,
        "config_id": configuration_id,
        "reserved": 0,
    }
    feature_id = (await create_resource(lm_api_client, feature_data, "/lm/features/"))["id"]
    print(f"Created feature with id: {feature_id}")

    print("Setup complete.")

    return {
        "configuration_id": configuration_id,
        "product_id": product_id,
    }


async def teardown(created_data: dict):
    """
    Tear down the License Manager API by deleting the resources created for the integration test.
    """
    print("Tearing down License Manager API...")

    await delete_resource(client=lm_api_client, resource_id=created_data["product_id"], resource_url="/lm/products")
    print(f"Deleted product with id: {created_data['product_id']}")

    # Cluster delete cascades to configurations, license servers, and features
    await delete_resource(
        client=lm_api_client, resource_id=created_data["configuration_id"], resource_url="/lm/configurations"
    )
    print(f"Deleted configuration with id: {created_data['configuration_id']}")

    print("Tear down complete.")
