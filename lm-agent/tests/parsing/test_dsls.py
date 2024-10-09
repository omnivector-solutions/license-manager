"""
Test the DSLS parser
"""

from pytest import mark

from lm_agent.parsing.dsls import parse, parse_feature_dict, parse_usage_dict
from lm_agent.models import LicenseUsesItem, ParsedFeatureItem


@mark.parametrize(
    "feature_dict,parsed_feature",
    [
        (
            {
                "Editor": "Dassault Systemes",
                "EditorId": "5E756A80",
                "Feature": "PAC",
                "Model": "Token",
                "Commercial Type": "STD",
                "Max Release Number": "8",
                "Max Release Date": "2025-01-01 00:59:00",
                "Pricing Structure": "YLC",
                "Max Casual Duration": "0",
                "Expiration Date": "2025-01-01 00:59:00",
                "Customer ID": "11723",
                "Count": "1",
                "Inuse": "0",
                "Tokens": "",
                "Casual Usage (mn)": None,
                "Host": None,
                "User": None,
                "Internal ID": None,
                "Active Process": None,
                "Client Code Version": None,
                "Session ID": None,
                "Granted Since": None,
                "Last Used At": None,
                "Granted At": None,
                "Queue Position": None,
            },
            ParsedFeatureItem(feature="pac", total=1, used=0, uses=[]),
        ),
        (
            {
                "Editor": "Dassault Systemes",
                "EditorId": "5E756A80",
                "Feature": "SRU",
                "Model": "Token",
                "Commercial Type": "STD",
                "Max Release Number": "423",
                "Max Release Date": "2025-01-01 00:59:00",
                "Pricing Structure": "YLC",
                "Max Casual Duration": "0",
                "Expiration Date": "2025-01-01 00:59:00",
                "Customer ID": "11723",
                "Count": "2374",
                "Inuse": "1559",
                "Tokens": "493",
                "Casual Usage (mn)": None,
                "Host": "nid00123 (0123.0)/127.0.0.1",
                "User": "user_1",
                "Internal ID": "SRU",
                "Active Process": "/powerflow/pf_sim_comm ( 48728)",
                "Client Code Version": "6.424",
                "Session ID": "2DBE16",
                "Granted Since": "2024-09-17 17:59:34",
                "Last Used At": "2024-09-18 15:25:50",
                "Granted At": "2024-09-17 17:59:34",
                "Queue Position": None,
            },
            ParsedFeatureItem(feature="sru", total=2374, used=1559, uses=[]),
        ),
        (
            {},
            None,
        ),
    ],
)
def test_parse_feature_dict(feature_dict, parsed_feature):
    """
    Does the parse_feature_dict function extracts the correct data from the csv line?
    The line contains several fields, but we only need:
    - feature
    - count
    - in_use
    """
    assert parse_feature_dict(feature_dict) == parsed_feature


@mark.parametrize(
    "usage_dict,parsed_usage",
    [
        (
            {
                "Editor": "Dassault Systemes",
                "EditorId": "5E756A80",
                "Feature": "PAC",
                "Model": "Token",
                "Commercial Type": "STD",
                "Max Release Number": "8",
                "Max Release Date": "2025-01-01 00:59:00",
                "Pricing Structure": "YLC",
                "Max Casual Duration": "0",
                "Expiration Date": "2025-01-01 00:59:00",
                "Customer ID": "11723",
                "Count": "1",
                "Inuse": "0",
                "Tokens": "",
                "Casual Usage (mn)": None,
                "Host": None,
                "User": None,
                "Internal ID": None,
                "Active Process": None,
                "Client Code Version": None,
                "Session ID": None,
                "Granted Since": None,
                "Last Used At": None,
                "Granted At": None,
                "Queue Position": None,
            },
            None,
        ),
        (
            {
                "Editor": "Dassault Systemes",
                "EditorId": "5E756A80",
                "Feature": "SRU",
                "Model": "Token",
                "Commercial Type": "STD",
                "Max Release Number": "423",
                "Max Release Date": "2025-01-01 00:59:00",
                "Pricing Structure": "YLC",
                "Max Casual Duration": "0",
                "Expiration Date": "2025-01-01 00:59:00",
                "Customer ID": "11723",
                "Count": "2374",
                "Inuse": "1559",
                "Tokens": "493",
                "Casual Usage (mn)": None,
                "Host": "nid00123 (0123.0)/127.0.0.1",
                "User": "user_1",
                "Internal ID": "SRU",
                "Active Process": "/powerflow/pf_sim_comm ( 48728)",
                "Client Code Version": "6.424",
                "Session ID": "2DBE16",
                "Granted Since": "2024-09-17 17:59:34",
                "Last Used At": "2024-09-18 15:25:50",
                "Granted At": "2024-09-17 17:59:34",
                "Queue Position": None,
            },
            LicenseUsesItem(username="user_1", lead_host="nid00123", booked=493),
        ),
        (
            {},
            None,
        ),
    ],
)
def test_parse_usage_dict(usage_dict, parsed_usage):
    """
    Does the parse_usage_dict function extracts the correct data from the csv line?
    The line contains:
    - user name
    - lead host
    - booked
    """
    assert parse_usage_dict(usage_dict) == parsed_usage


def test_parse__correct_output(dsls_output):
    """
    Does the parser return the correct data for this output?
    - dsls_output: expected output from the license server,
    which contain licenses and usage information.
    """
    assert parse(dsls_output) == {
        "pac": ParsedFeatureItem(feature="pac", total=1, used=0, uses=[]),
        "paj": ParsedFeatureItem(feature="paj", total=6, used=0, uses=[]),
        "pca": ParsedFeatureItem(feature="pca", total=4, used=0, uses=[]),
        "pco": ParsedFeatureItem(feature="pco", total=2, used=0, uses=[]),
        "pd5": ParsedFeatureItem(feature="pd5", total=1, used=0, uses=[]),
        "pv6": ParsedFeatureItem(feature="pv6", total=7, used=0, uses=[]),
        "pvg": ParsedFeatureItem(feature="pvg", total=2, used=0, uses=[]),
        "pw7": ParsedFeatureItem(
            feature="pw7",
            total=2000,
            used=2,
            uses=[LicenseUsesItem(username="user_1", lead_host="nid001627", booked=2)],
        ),
        "pw8": ParsedFeatureItem(feature="pw8", total=2000, used=0, uses=[]),
        "sru": ParsedFeatureItem(
            feature="sru",
            total=2374,
            used=1559,
            uses=[
                LicenseUsesItem(username="user_2", lead_host="nid001626", booked=493),
                LicenseUsesItem(username="user_3", lead_host="nid001601", booked=533),
                LicenseUsesItem(username="user_4", lead_host="nid001671", booked=533),
            ],
        ),
    }


def test_parse__bad_output(dsls_output_bad):
    """
    Does the parser return the correct data for this output?
    - dsls_output_bad: unparseable output from the license server,
    which can happen when a connection error occours.
    """
    assert parse(dsls_output_bad) == {}


def test_parse__no_licenses_output(dsls_output_no_licenses):
    """
    Does the parser return the correct data for this output?
    - dsls_output_no_licenses: expected output from the server
    when none of the licenses are in use by users.
    """
    assert parse(dsls_output_no_licenses) == {
        "pac": ParsedFeatureItem(feature="pac", total=1, used=0, uses=[]),
        "paj": ParsedFeatureItem(feature="paj", total=6, used=0, uses=[]),
        "pca": ParsedFeatureItem(feature="pca", total=4, used=0, uses=[]),
        "pco": ParsedFeatureItem(feature="pco", total=2, used=0, uses=[]),
        "pd5": ParsedFeatureItem(feature="pd5", total=1, used=0, uses=[]),
        "pv6": ParsedFeatureItem(feature="pv6", total=7, used=0, uses=[]),
        "pvg": ParsedFeatureItem(feature="pvg", total=2, used=0, uses=[]),
        "pw7": ParsedFeatureItem(feature="pw7", total=2000, used=0, uses=[]),
        "pw8": ParsedFeatureItem(feature="pw8", total=2000, used=0, uses=[]),
        "sru": ParsedFeatureItem(feature="sru", total=2374, used=0, uses=[]),
    }
