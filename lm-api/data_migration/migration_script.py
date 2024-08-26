from typing import List 
from loguru import logger
import httpx
from data_migration.exceptions import AuthTokenError, BadResponse
from dotenv import load_dotenv
import os
from data_migration.models import OldConfiguration


load_dotenv()


def acquire_token(oidc_domain, client_id, client_secret) -> str:
    """
    Retrieves a token from OIDC.
    """
    logger.debug("Attempting to acquire token from OIDC")
    oidc_body = dict(
        client_id=client_id,
        client_secret=client_secret,
        grant_type="client_credentials",
    )
    oidc_url = f"{oidc_domain}/protocol/openid-connect/token"
    logger.debug(f"Posting OIDC request to {oidc_url}")
    response = httpx.post(oidc_url, data=oidc_body)
    AuthTokenError.require_condition(
        response.status_code == 200, f"Failed to get auth token from OIDC: {response.text}"
    )
    with AuthTokenError.handle_errors("Malformed response payload from OIDC"):
        token = response.json()["access_token"]

    logger.debug("Successfully acquired auth token from OIDC")

    return token


def get_old_configurations(token: str) -> List[OldConfiguration]:
    """
    Fetches all configurations from the old backend.
    """
    logger.debug("Fetching all configurations from old backend")

    url = f"{os.environ.get('OLD_BACKEND_BASE_URL')}/lm/api/v1/config/all"

    response = httpx.get(
        url=url,
        headers={"Authorization": f"Bearer {token}"}
    )

    BadResponse.require_condition(
        response.status_code == 200, f"Failed to get configs: {response.text}"
    )

    with BadResponse.handle_errors("Malformed response payload from API"):
        return [OldConfiguration(**configuration) for configuration in response.json()]
    

def parse_old_configurations(old_configurations: List[OldConfiguration]) -> List[dict]:
    """
    Parsed all the old configurations into the new data structure.
    """
    parsed_configurations = []

    for configuration in old_configurations:
        configuration_name = configuration.name
        product = configuration.product
        
        features = [{
            "name": feature,
            "reserved": configuration.features[feature]["total"] - configuration.features[feature]["limit"], 
        } for feature in configuration.features.keys()]
        
        license_servers = [{
            "host": license_server.split(":")[1],
            "port": license_server.split(":")[2],
        } for license_server in configuration.license_servers]

        grace_time = configuration.grace_time
        type = configuration.license_server_type
        client_id = configuration.client_id

        parsed_configurations.append({
            "name": configuration_name,
            "client_id": client_id,
            "product": product,
            "features": features,
            "license_servers": license_servers,
            "grace_time": grace_time,
            "type": type,
        })

    return parsed_configurations


def create_product_or_get_id(token: str, product_name: str) -> int:
    """
    Create a new product or get the id of an existing one.
    """
    products_url = f"{os.environ.get('NEW_BACKEND_BASE_URL')}/lm/products"

    response = httpx.get(
        url=products_url,
        headers={"Authorization": f"Bearer {token}"}
    )

    BadResponse.require_condition(
        response.status_code == 200, f"Failed to get products: {response.text}"
    )

    with BadResponse.handle_errors("Malformed response payload from API"):
        products = response.json()

    for product in products:
        if product["name"] == product_name:
            return product["id"]

    response = httpx.post(
        url=products_url,
        headers={"Authorization": f"Bearer {token}"},
        json={"name": product_name}
    )

    BadResponse.require_condition(
        response.status_code == 201, f"Failed to create product: {response.text}"
    )

    with BadResponse.handle_errors("Malformed response payload from API"):
        return response.json()["id"]


def create_new_configurations(token: str, old_configurations: List[OldConfiguration]):
    """
    Create all configurations in the new format using the old configurations data.

    Each configuration can have the resources:
    - License server(s)
    - Feature(s)

    The Feature must have a Product. If it doesn't exist yet, it'll be created.
    """
    configurations_url = f"{os.environ.get('NEW_BACKEND_BASE_URL')}/lm/configurations"
    
    for configuration in old_configurations:
        logger.debug(f"Creating configuration {configuration['name']}")
        product_id = create_product_or_get_id(token=token, product_name=configuration["product"])

        features_payload = [
            {
                "name": feature["name"],
                "product_id": product_id,
                "reserved": feature["reserved"]
            } for feature in configuration["features"]
        ]
        
        configuration_payload = {
            "name": configuration["name"],
            "cluster_client_id": configuration["client_id"],
            "grace_time": configuration["grace_time"],
            "type": configuration["type"],
            "license_servers": configuration["license_servers"],
            "features": features_payload
        }

        try:
            response = httpx.post(
                url=configurations_url,
                headers={"Authorization": f"Bearer {token}"},
                json=configuration_payload,
            )
            BadResponse.require_condition(
                response.status_code == 201, f"Failed to create configuration: {response.text}"
            )
        except BadResponse:
            logger.debug("Failed to create configuration in new backend")


def main():
    old_token = acquire_token(
        oidc_domain=os.environ.get("OLD_OIDC_DOMAIN"),
        client_id=os.environ.get("OLD_OIDC_CLIENT_ID"),
        client_secret=os.environ.get("OLD_OIDC_CLIENT_SECRET"),
    )

    new_token = acquire_token(
        oidc_domain=os.environ.get("NEW_OIDC_DOMAIN"),
        client_id=os.environ.get("NEW_OIDC_CLIENT_ID"),
        client_secret=os.environ.get("NEW_OIDC_CLIENT_SECRET"),
    )

    old_configurations = get_old_configurations(token=old_token)
    parsed_configurations = parse_old_configurations(old_configurations)
    create_new_configurations(token=new_token, old_configurations=parsed_configurations)


if __name__ == "__main__":
    main()
