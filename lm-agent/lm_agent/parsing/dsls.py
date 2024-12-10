"""
Parser for DSLS.
"""
import csv
from typing import Optional

from lm_agent.models import LicenseUsesItem, ParsedFeatureItem


def parse_feature_dict(feature_dict: dict[str, str]) -> Optional[ParsedFeatureItem]:
    """
    Parse the feature dcit in the DSLS output.

    Data we need:
    - ``feature``: license name
    - ``total``: total amount of licenses
    - ``used``: quantity of licenses being used
    """
    if not all([feature_dict.get("Feature"), feature_dict.get("Count"), feature_dict.get("Inuse")]):
        return None

    return ParsedFeatureItem(
        feature=feature_dict["Feature"].lower(),
        total=int(feature_dict["Count"]),
        used=int(feature_dict["Inuse"]),
        uses=[],
    )


def parse_usage_dict(usage_dict: dict[str, str]) -> Optional[LicenseUsesItem]:
    """
    Parse the usage dict in the DSLS output.

    Data we need:
    - ``username``: user who booked the license
    - ``lead_host``: host using the license
    - ``booked``: quantity of licenses being used
    """
    if not all([usage_dict.get("User"), usage_dict.get("Host"), usage_dict.get("Tokens")]):
        return None

    return LicenseUsesItem(
        username=usage_dict["User"],
        lead_host=usage_dict["Host"].split()[0],
        booked=int(usage_dict["Tokens"]),
    )


def parse(server_output: str) -> dict[str, ParsedFeatureItem]:
    """
    Parse the output from the DSLS server.
    Data we need:
    - ``feature``: license name
    - ``count``: total amount of licenses
    - ``in_use``: quantity of licenses being use
    - ``uses``: list of users using the license

    Obs: if the feature is used by multiple users, each usage will result in a line
    with the same feature information, just changing the usage data.
    """
    parsed_data: dict = {}

    # Ignore the lines that contain information about the DSLS license server
    if "Warning" in server_output:  # Remove warning line with the information lines
        offset = 7
    else:
        offset = 6

    csv_data = csv.DictReader(server_output.splitlines()[offset:])

    for row in csv_data:
        parsed_feature = parse_feature_dict(row)
        if not parsed_feature:
            continue

        parsed_usage = parse_usage_dict(row)
        if parsed_usage:
            parsed_feature.uses.append(parsed_usage)

        if parsed_feature.feature in parsed_data:
            parsed_data[parsed_feature.feature].uses.extend(parsed_feature.uses)
        else:
            parsed_data[parsed_feature.feature] = parsed_feature

    return parsed_data
