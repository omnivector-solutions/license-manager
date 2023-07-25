from lm_test.utils import run
from lm_test.config import settings


def setup():
    """
    Setup the cluster where the integration test will run.
    """
    print("Setting up cluster...")

    print("Backing up license server paths...")
    # backup the license server paths before changing it with LM-SIM
    license_servers_configs = [
        "lmutil-path",
        "rlmutil-path",
        "lsdyna-path",
        "lmxendutil-path",
        "olixtool-path",
    ]

    backed_up_license_servers = {}

    for license_server in license_servers_configs:
        old_path = run(
            "juju",
            "config",
            "license-manager-agent",
            license_server,
        )
        backed_up_license_servers[license_server] = old_path
        print(f"{license_server} path backed up")

    print("Setting up LM-SIM...")
    # set the lmutil path to the fake one use by LM-SIM
    run(
        "make",
        "setup",
        "-C",
        str(settings.LM_SIM_PATH),
        f"lm_sim_ip={settings.LM_SIM_BASE_URL}",
    )
    print("LM-SIM setup complete")

    print("Triggering reconciliation...")
    # run reconciliation to update license counters
    run(
        "juju",
        "ssh",
        "license-manager-agent/leader",
        "sudo",
        "/bin/bash",
        "-c",
        "'source",
        "/srv/license-manager-agent-venv/bin/activate",
        "&&",
        "reconcile'",
    )
    print("Reconciliation done")

    print("Setup complete.")
    return backed_up_license_servers


def teardown(license_servers_backup):
    """
    Teardown the cluster where the integration test ran.
    """
    print("Tearing down cluster...")

    print("Restoring license server paths...")
    # restore the license server paths
    for license_server, old_path in license_servers_backup.items():
        run(
            "juju",
            "config",
            "license-manager-agent",
            f"{license_server}={old_path}",
        )
        print(f"{license_server} path restored")

    print("Deleting fake license from cluster...")
    # delete the fake license from the cluster
    run(
        "juju",
        "ssh",
        "license-manager-agent/leader",
        "sudo",
        "sacctmgr",
        "delete",
        "resource",
        "test_product.test_feature",
        "-i",
    )
    print("Fake license deleted")

    print("Deleting fake job from cluster...")
    # delete the fake job created by LM-SIM
    run(
        "juju",
        "ssh",
        "slurmd/leader",
        "sudo",
        "rm",
        "/tmp/batch.sh",
        "&&"
        "rm",
        "/tmp/application.sh",
    )
    print("Fake job deleted")

    print("Teardown complete.")
