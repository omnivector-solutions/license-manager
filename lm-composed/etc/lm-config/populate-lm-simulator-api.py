#!/app/lm-agent/.venv/bin/python
import httpx


LM_SIMULATOR_BASE_URL = "http://lm-simulator-api:8000"


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


def clean_table(table_name, key):
    response = httpx.get(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}")
    rows = handle_request_errors(response)

    for row in rows:
        identifier = row[key]
        delete_response = httpx.delete(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}/{identifier}")
        handle_request_errors(delete_response)


def create_data(table_name, data):
    response = httpx.post(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}", json=data)
    return handle_request_errors(response)


def main():
    clean_table("licenses", "name")
    license_data = {"name": "test_feature", "total": 1000, "license_server_type": "flexlm"}
    create_data("licenses", license_data)

    clean_table("licenses-in-use", "license_name")
    license_in_use_data = {
        "quantity": 50,
        "user_name": "test_user",
        "lead_host": "test_host",
        "license_name": "test_feature",
    }
    create_data("licenses-in-use", license_in_use_data)


if __name__ == "__main__":
    main()
