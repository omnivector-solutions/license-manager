#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the FlexLM,
this way we can use the same flexlm parser in the license-manager-agent.
"""
import requests
from jinja2 import Environment, FileSystemLoader

# You must modify this value to reflect the ip address and port that the
# license-manager-simulator is listening on in your environment.
#
# The format of the value is: `http://<ip-address>:<port>`
URL = "http://localhost:8000"


def get_server_data():
    """
    To simulate the FlexLM output, add this license to the backend:
    {
        "name": "abaqus",
        "total": 1000
    }
    Since FlexLM outputs only the ``feature`` name (omitting the ``product``), the license
    in the simulator database should be created with the feature as its name.
    """
    licenses = requests.get(URL + "/lm-sim/licenses/").json()

    for license in licenses:
        if license["name"] == "abaqus":
            return {
                "license_name": license.get("name"),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "licenses_in_use": license.get("licenses_in_use"),
            }


def generate_license_server_output() -> None:
    """Print output formatted to stdout."""
    source = "lmutil.out.tmpl"
    license_information = get_server_data()

    template = Environment(loader=FileSystemLoader(".")).get_template(source)
    print(template.render(**license_information))


if __name__ == "__main__":
    generate_license_server_output()
