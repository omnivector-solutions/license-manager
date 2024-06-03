#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the RLM,
this way we can use the same rlm parser in the license-manager-agent.
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
    To simulate the RLM output, add this license to the backend:
    {
        "name": "converge_super",
        "total": 1000
    }
    Since RLM outputs the feature name as the product and feature concatenated with a underscore,
    the license in the simulator database should be named with two words concatenated by ``_``.
    """
    licenses = requests.get(URL + "/lm-sim/licenses/").json()

    for license in licenses:
        if license["name"] == "converge_super":
            any_in_use = license["in_use"] > 0
            return {
                "license_name": license.get("name"),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "licenses_in_use": license.get("licenses_in_use"),
                "any_in_use": any_in_use,
            }


def generate_license_server_output() -> None:
    """Print output formatted to stdout."""
    source = "rlmutil.out.tmpl"
    licenses_information = get_server_data()

    template = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True).get_template(
        source
    )
    print(template.render(**licenses_information))


if __name__ == "__main__":
    generate_license_server_output()
