#!/app/lm-agent/.venv/bin/python
import subprocess
import shlex


LICENSE_NAME = "test_product.test_feature"
SERVER_TYPE = "flexlm"


def main():
    cmd = shlex.split(f"scontrol show lic {LICENSE_NAME}@{SERVER_TYPE}")
    output = subprocess.run(cmd, capture_output=True)
    stdout = output.stdout.decode("utf-8")

    if f"{LICENSE_NAME}@{SERVER_TYPE}" in stdout:
        return
    else:
        cmd = shlex.split(
            f"sacctmgr add resource Type=license Clusters=linux Server={SERVER_TYPE} "
            f"Names={LICENSE_NAME} Count=1000 ServerType={SERVER_TYPE} PercentAllowed=100 -i"
        )
        output = subprocess.run(cmd, capture_output=True)
        return_code = output.returncode

        if return_code != 0:
            print(f"Failed to create license, return code: {return_code}")
            exit(1)


if __name__ == "__main__":
    main()
