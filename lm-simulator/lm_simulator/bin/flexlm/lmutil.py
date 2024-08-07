#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the FlexLM,
this way we can use the same flexlm parser in the license-manager-agent.
"""
import sys
from pathlib import Path

import requests
from jinja2 import Environment, FileSystemLoader


def get_server_data(lm_sim_host: str, lm_sim_port: str) -> dict:
    """
    To simulate the FlexLM output, add this license to the backend:
    {
        "name": "abaqus",
        "total": 1000
    }
    Since FlexLM outputs only the ``feature`` name (omitting the ``product``), the license
    in the simulator database should be created with the feature as its name.
    """
    licenses = requests.get(f"http://{lm_sim_host}:{lm_sim_port}/lm-sim/licenses/").json()

    for license in licenses:
        if license["name"] == "abaqus":
            return {
                "license_name": license.get("name"),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "licenses_in_use": license.get("licenses_in_use"),
            }


def generate_license_server_output(license_information: dict) -> None:
    """Print output formatted to stdout."""
    script_path = Path(__file__).resolve()
    template_dir = script_path.parent
    source = "lmutil.out.tmpl"

    template = Environment(loader=FileSystemLoader(str(template_dir))).get_template(source)
    print(template.render(**license_information))


def main():
    """
    License Manager Agent will invoke the lmutil binary with the following arguments:
    ```
    lmutil lmstat -c <port>@<host> -f <feature>
    ```
    The license server host and port will be identify the License Manager Simulator API.
    """
    assert len(sys.argv) == 6, "Invalid number of arguments"

    lm_sim_host = sys.argv[3].split("@")[1]
    lm_sim_port = sys.argv[3].split("@")[0]

    license_information = get_server_data(lm_sim_host, lm_sim_port)
    generate_license_server_output(license_information)


if __name__ == "__main__":
    main()
