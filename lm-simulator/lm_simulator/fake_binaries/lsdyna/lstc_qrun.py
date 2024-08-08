#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the LS-Dyna,
this way we can use the same LS-Dyna parser in the license-manager-agent.
"""

import sys
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


def get_server_data(lm_sim_host: str, lm_sim_port: str) -> dict:
    """
    To simulate the LS-Dyna output, add a license with ``lsdyna``license server type to the backend:
    {
        "name": "MPPDYNA",
        "total": 1000,
        "license_server_type": "lsdyna"
    }
    Since LS-Dyna outputs the feature name with all letters in uppercase,
    the license in the simulator database should be named in uppercase as well.
    """
    response = requests.get(f"http://{lm_sim_host}:{lm_sim_port}/lm-sim/licenses/type/lsdyna")
    if response.status_code != 200:
        exit(1)
    licenses = response.json()

    return {
        "licenses": [
            {
                "license_name": license.get("name").upper(),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "licenses_in_use": license.get("licenses_in_use"),
                "free": int(license.get("total")) - int(license.get("in_use")),
                "used": "-" if len(license.get("licenses_in_use")) > 0 else 0,
            }
            for license in licenses
        ]
    }


def generate_license_server_output(license_information: dict) -> None:
    """Print output formatted to stdout."""
    script_path = Path(__file__).resolve()
    template_dir = script_path.parent
    source = "lstc_qrun.out.tmpl"

    template = Environment(
        loader=FileSystemLoader(str(template_dir)), trim_blocks=True, lstrip_blocks=True
    ).get_template(source)
    print(template.render(**license_information))


def main():
    """
    License Manager Agent will invoke the lstc_qrun binary with the following arguments:
    ```
    lstc_qrun -s <port>@<host> -R
    ```
    The license server host and port will identify the License Manager Simulator API.
    """
    assert len(sys.argv) == 4, "Invalid number of arguments"

    lm_sim_port, lm_sim_host = sys.argv[2].split("@")

    license_information = get_server_data(lm_sim_host, lm_sim_port)
    generate_license_server_output(license_information)


if __name__ == "__main__":
    main()
