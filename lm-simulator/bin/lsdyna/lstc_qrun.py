#!/usr/bin/env python3
"""
File that will be called by the license-manager-agent in the report function.

It will hit the /licenses-in-use/ endpoint and will generate the report in the same format as the LS-Dyna,
this way we can use the same LS-Dyna parser in the license-manager-agent.
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
    To simulate the LS-Dyna output, add this license to the backend:
    {
        "name": "MPPDYNA",
        "total": 1000
    }
    Since LS-Dyna outputs the feature name with all letters in uppercase,
    the license in the simulator database should be named in uppercase as well.
    """
    licenses = requests.get(URL + "/lm-sim/licenses/").json()

    for license in licenses:
        if license["name"] == "MPPDYNA":
            used = "-" if len(license["licenses_in_use"]) > 0 else 0
            return {
                "license_name": license.get("name").upper(),
                "total_licenses": license.get("total"),
                "in_use": license.get("in_use"),
                "free": int(license.get("total")) - int(license.get("in_use")),
                "licenses_in_use": license.get("licenses_in_use"),
                "used": used,
            }


def generate_license_server_output():
    """Print output formatted to stdout."""
    source = "lstc_qrun.out.tmpl"
    license_information = get_server_data()

    template = Environment(loader=FileSystemLoader("."), trim_blocks=True, lstrip_blocks=True).get_template(
        source
    )
    print(template.render(**license_information))


if __name__ == "__main__":
    generate_license_server_output()
