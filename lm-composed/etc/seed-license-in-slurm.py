#!/app/lm-agent/.venv/bin/python
import subprocess


LICENSE_NAME = "test_product.test_feature"
SERVER_TYPE = "flexlm"


def main():
    output = subprocess.run([
        "scontrol",
        "show",
        "lic",
        f"{LICENSE_NAME}@{SERVER_TYPE}",
    ], capture_output=True)

    stdout = output.stdout.decode("utf-8")

    if "test_product.test_feature@flexlm" in stdout:
        return
    else:
        output = subprocess.run([
            "sacctmgr",
            "add",
            "resource",
            "Type=license",
            "Clusters=linux",
            f"Server={SERVER_TYPE}",
            f"Names={LICENSE_NAME}",
            "Count=1000",
            f"ServerType={SERVER_TYPE}",
            "PercentAllowed=100",
            "-i",
        ])

        return_code = output.returncode
        if return_code != 0:
            print(f"Failed to create license, return code: {return_code}")
            exit(1)


if __name__ == "__main__":
    main()
