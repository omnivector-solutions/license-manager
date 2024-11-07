#!/app/lm-agent/.venv/bin/python
import httpx
import os

LM_AGENT_OIDC_DOMAIN = os.getenv("LM_AGENT_OIDC_DOMAIN")
LM_AGENT_OIDC_CLIENT_ID = os.getenv("LM_AGENT_OIDC_CLIENT_ID")
LM_AGENT_OIDC_CLIENT_SECRET = os.getenv("LM_AGENT_OIDC_CLIENT_SECRET")
LM_AGENT_BACKEND_BASE_URL = os.getenv("LM_AGENT_BACKEND_BASE_URL")


def handle_request_errors(response):
    try:
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        print(f"Request to {response.request.url} failed with: {e.response.status_code} - {e.response.text}")
        exit(1)
    except KeyError:
        print("Unexpected response format; JSON data could not be parsed.")
        exit(1)


def get_access_token():
    response = httpx.post(
        f"http://{LM_AGENT_OIDC_DOMAIN}/protocol/openid-connect/token",
        data={
            "client_id": LM_AGENT_OIDC_CLIENT_ID,
            "client_secret": LM_AGENT_OIDC_CLIENT_SECRET,
            "grant_type": "client_credentials"
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    return handle_request_errors(response)["access_token"]


def clean_table(token, table_name):
    response = httpx.get(
        f"{LM_AGENT_BACKEND_BASE_URL}/lm/{table_name}",
        headers={"Authorization": f"Bearer {token}"}
    )
    rows = handle_request_errors(response)

    for row in rows:
        _id = row["id"]
        delete_response = httpx.delete(
            f"{LM_AGENT_BACKEND_BASE_URL}/lm/{table_name}/{_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        handle_request_errors(delete_response)


def create_data(token, table_name, data):
    response = httpx.post(
        f"{LM_AGENT_BACKEND_BASE_URL}/lm/{table_name}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json=data
    )
    return handle_request_errors(response)


def main():
    access_token = get_access_token()

    clean_table(access_token, "products")
    product_data = {"name": "test_product"}
    product_id = create_data(access_token, "products", product_data)["id"]

    clean_table(access_token, "configurations")
    configuration_data = {
        "name": "test_feature",
        "cluster_client_id": LM_AGENT_OIDC_CLIENT_ID,
        "features": [
            {
                "name": "test_feature",
                "product_id": product_id,
                "reserved": 0
            }
        ],
        "license_servers": [
            {
                "host": "lm-simulator-api",
                "port": 8000
            }
        ],
        "grace_time": 300,
        "type": "flexlm"
    }
    create_data(access_token, "configurations", configuration_data)


if __name__ == "__main__":
    main()
