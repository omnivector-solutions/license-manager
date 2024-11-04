#!/app/lm-agent/.venv/bin/python
import httpx


LM_SIMULATOR_BASE_URL = "http://lm-simulator-api:8000"


def clean_table(table_name, key):
    rows = httpx.get(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}").json()

    for row in rows:
        identifier = row[key]
        httpx.delete(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}/{identifier}")


def create_data(table_name, data):
    return httpx.post(f"{LM_SIMULATOR_BASE_URL}/lm-sim/{table_name}", json=data).json()


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
