"""
Run the integration test.
"""
import asyncio
from lm_test.cluster_interface import setup as cluster_setup, teardown as cluster_teardown
from lm_test.lm_api_interface import setup as lm_api_setup, teardown as lm_api_teardown
from lm_test.run_job import submit_job


async def main():
    """
    Run the integration test.

    Setup the LM_API:
        - create a cluster in the API for the test cluster;
        - add the fake license (test_product.test_feature) configuration to the API;

    Setup LM-SIM in the cluster:
        - change the license servers paths to the fake ones use by LM-SIM;
        - add the fake license (test_product.test_feature) to LM-SIM;
        - add the fake license (test_product.test_feature) to the cluster;
        - copy the fake job to slurmd node;

    Submit the fake job to the cluster:
        - the fake job will use the fake license (test_product.test_feature);

    Teardown the LM_API:
        - delete the fake license (test_product.test_feature) configuration from the API;
        - delete the cluster in the API;

    Teardown LM-SIM in the cluster:
        - restore the license servers paths;
        - delete the fake license (test_product.test_feature) from LM-SIM;
        - delete the fake job from the slurmd node;
"""
    print("Starting integration test...")

    lm_api_created_data = await lm_api_setup()
    cluster_backed_up_data = cluster_setup()

    submit_job()

    cluster_teardown(cluster_backed_up_data)
    await lm_api_teardown(lm_api_created_data)

    print("Integration test finished.")


if __name__ == "__main__":
    asyncio.run(main())
