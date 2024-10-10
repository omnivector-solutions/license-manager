#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the DSÇS,
this way we can use the same DSLS parser in the license-manager-agent.
"""

import sys
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


def get_server_data(lm_sim_host: str, lm_sim_port: str) -> dict:
    """
    To simulate the DSLS output, add a license with ``dsls`` license server type to the backend:
    {
        "name": "Powerflow",
        "total": 1000,
        "license_server_type": "dsls"
    }
    Since DSLS outputs only the ``feature`` name (omitting the ``product``), the license
    in the simulator database should be created with the feature as its name.
    """
    response = requests.get(f"http://{lm_sim_host}:{lm_sim_port}/lm-sim/licenses/type/dsls")
    if response.status_code != 200:
        exit(1)
    licenses = response.json()

    return {
        "licenses": [
            {
                "license_name": license.get("name"),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "licenses_in_use": license.get("licenses_in_use"),
            }
            for license in licenses
        ]
    }


def generate_license_server_output(license_information: dict) -> None:
    """Print output formatted to stdout."""
    script_path = Path(__file__).resolve()
    template_dir = script_path.parent
    source = "DSLicSrv.out.tmpl"

    template = Environment(
        loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True
    ).get_template(source)
    print(template.render(**license_information))


def main():
    """
    License Manager Agent will invoke the DSLicSrv binary with the following arguments:
    ```
    echo -e "connect <host> <port> \ngetLicenseUsage -csv" | DSLicSrv -admin
    ```
    The license server host and port will be identify the License Manager Simulator API.
    """
    input_data = sys.stdin.read().split()
    assert len(input_data) == 5, "Invalid number of arguments"

    lm_sim_host = input_data[1]
    lm_sim_port = input_data[2]

    license_information = get_server_data(lm_sim_host, lm_sim_port)
    generate_license_server_output(license_information)


if __name__ == "__main__":
    main()
