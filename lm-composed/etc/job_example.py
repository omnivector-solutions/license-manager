#!/usr/bin/env python3

#SBATCH --partition=compute
#SBATCH -N 1
#SBATCH --job-name=job_example
#SBATCH --output=/nfs/%j.out
#SBATCH --error=/nfs/%j.err
#SBATCH --licenses=test_product.test_feature@flexlm:42

import json
import random
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request
from time import sleep


URL = "http://lm-simulator-api:8000"


def make_request(url, method="GET", data=None, headers=None):
    """Make an HTTP request and return the response."""
    if data is not None:
        data = json.dumps(data).encode("utf-8")

    if headers is None:
        headers = {"Content-Type": "application/json"}

    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request) as response:
            return response.getcode(), response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Unknown Error: {e}")
        sys.exit(1)


def main():
    payload = {
        "quantity": 42,
        "user_name": "test_user",
        "lead_host": socket.gethostname(),
        "license_name": "test_feature",
    }

    print(f"Requesting {payload['quantity']} licenses for user {payload['user_name']}")

    response_status, response_body = make_request(
        f"{URL}/lm-sim/licenses-in-use", method="POST", data=payload
    )

    if response_status == 201:
        sleep_time = random.randint(60, 120)
        print(f"There are enough licenses available, let's run (sleep) the job for {sleep_time} seconds")
        sleep(sleep_time)
    else:
        print("There are not enough licenses, let's crash the job")
        sys.exit("NOT_ENOUGH_LICENSES")

    license_in_use_id = json.loads(response_body).get("id")

    print(f"Deleting the license-in-use record with id {license_in_use_id}")

    response_status, _ = make_request(f"{URL}/lm-sim/licenses-in-use/{license_in_use_id}", method="DELETE")

    if response_status != 204:
        print("Failed to delete license-in-use")
        sys.exit("FAILED_TO_DELETE_LICENSE_IN_USE")

    print("Job done")


if __name__ == "__main__":
    main()
