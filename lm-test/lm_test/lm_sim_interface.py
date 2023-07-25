from lm_test.utils import LM_SIM_Client, create_resource, delete_resource
import asyncio


lm_sim_client = LM_SIM_Client()


async def setup():
    """
    Set up the License Manager Simulator with the resouces needed for the integration test.
    """
    license_data = {
        "name": "test_feature",
        "total": 1000,
    }

    created_license = await create_resource(lm_sim_client, license_data, "/lm-sim/licenses/")
    print(f"Created license with id: {created_license['id']}")

    in_use_data = {
        "quantity": 500,
        "user_name": "user1",
        "lead_host": "host1",
        "license_name": "test_feature"
    }

    created_in_use = await create_resource(lm_sim_client, in_use_data, "/lm-sim/licenses-in-use/")
    print(f"Created in-use with id: {created_in_use['id']}")

    print("Setup complete.")

    return {
        "license_name": created_license["name"],
        "quantity": created_in_use["quantity"],
        "user_name": created_in_use["user_name"],
        "lead_host": created_in_use["lead_host"],
    }


async def teardown(created_data):
    """
    Tear down the License Manager Simulator by deleting the resources created for the integration test.
    """
    await delete_resource(client=lm_sim_client, resource_id=None, resource_url="/lm-sim/licenses-in-use/", payload=created_data)
    print(f"Deleted in-use for license: {created_data['license_name']}")
    await delete_resource(client=lm_sim_client, resource_id=created_data["license_name"], resource_url="/lm-sim/licenses")
    print(f"Deleted in-use for license: {created_data['license_name']}")

    print("Teardown complete.")


async def main():
    created_data = await setup()
    await teardown(created_data)

if __name__ == "__main__":
    asyncio.run(main())
