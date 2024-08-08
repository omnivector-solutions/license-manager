#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the OLicense,
this way we can use the same LM-X parser in the license-manager-agent.
"""

import sys
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


def get_server_data(lm_sim_host: str, lm_sim_port: str) -> dict:
    """
    To simulate the OLicense output, add a license with ``olicense`` license server type to the backend:
    {
        "name": "ftire_adams",
        "total": 1000,
        "license_server_type": "olicense"
    }
    Since OLicense outputs only the ``feature`` name (omitting the ``product``), the license
    in the simulator database should be created with the feature as its name.
    """
    response = requests.get(f"http://{lm_sim_host}:{lm_sim_port}/lm-sim/licenses/type/olicense")
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
                "any_in_use": license.get("in_use") > 0,
            }
            for license in licenses
        ]
    }


def generate_license_server_output(license_information: dict) -> None:
    """Print output formatted to stdout."""
    script_path = Path(__file__).resolve()
    template_dir = script_path.parent
    source = "olixtool.out.tmpl"

    template = Environment(
        loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True
    ).get_template(source)
    print(template.render(**license_information))


def main():
    """
    License Manager Agent will invoke the olixtool binary with the following arguments:
    ```
    olixtool -sv <host>:<port>
    ```
    The license server host and port will be identify the License Manager Simulator API.
    """
    assert len(sys.argv) == 3, "Invalid number of arguments"

    lm_sim_host, lm_sim_port = sys.argv[2].split(":")

    license_information = get_server_data(lm_sim_host, lm_sim_port)
    generate_license_server_output(license_information)


if __name__ == "__main__":
    main()
