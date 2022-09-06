"""
Pydantic models for various data items.
"""

import json
import re
from json.decoder import JSONDecodeError
from typing import List, Optional

import httpx
import pydantic

from lm_cli.exceptions import Abort
from lm_cli.text_tools import dedent


class TokenSet(pydantic.BaseModel, extra=pydantic.Extra.ignore):
    """
    A model representing a pairing of access and refresh tokens.
    """

    access_token: str
    refresh_token: Optional[str] = None


class IdentityData(pydantic.BaseModel):
    """
    A model representing the fields that should appear in our custom identity data claim.
    """

    user_email: str
    org_name: Optional[str]


class Persona(pydantic.BaseModel):
    """
    A model representing a pairing of a TokenSet and Identity data.

    This is a convenience to combine all of the identifying data and credentials for a given user.
    """

    token_set: TokenSet
    identity_data: IdentityData


class DeviceCodeData(pydantic.BaseModel, extra=pydantic.Extra.ignore):
    """
    A model representing the data that is returned from OIDC's device code endpoint.
    """

    device_code: str
    verification_uri_complete: str
    interval: int


class LicenseManagerContext(pydantic.BaseModel, arbitrary_types_allowed=True):
    """
    A data object describing context passed from the main entry point.
    """

    persona: Optional[Persona]
    client: Optional[httpx.Client]


class ConfigurationCreateRequestData(pydantic.BaseModel):
    """
    Describe the data that will be sent to the ``create`` endpoint of the LM API for configurations.
    """

    name: str
    product: str
    features: str
    license_servers: List[str]
    license_server_type: str
    grace_time: str
    client_id: str

    @pydantic.validator("features", pre=True)
    def validate_features_is_valid_json(cls, features):
        """
        Validate the feature field to ensure it contains a valid JSON serialized object.
        The expected format is a string containing a JSON object.
        Example: ``"{\"feature\": 1}"``.
        """
        try:
            json.loads(features)
        except JSONDecodeError:
            raise Abort(
                """
                You must supply the [yellow]features[/yellow] as a string with a valid JSON object serialized.
                """,
                subject="Invalid features parameter.",
            )
        return features

    @pydantic.validator("license_servers", pre=True)
    def validate_license_servers_are_valid_connection_strings(cls, license_servers):
        """
        Validate the license servers list to ensure each entry is in the correct format.
        The expected format is: <license_server_type>:<hostname>:<port>.
        Example: ``flexlm:127.0.0.1:1234``.
        """
        LICENSE_SERVER_LINE = r"[a-z]+:[a-zA-Z0-9-]+(\.[a-zA-Z0-9]+)*:[0-9]*"
        LICENSE_SERVER_RX = re.compile(LICENSE_SERVER_LINE)

        license_servers_list = license_servers.split(",")

        for license_server in license_servers_list:
            valid_license_server = LICENSE_SERVER_RX.match(license_server)
            if valid_license_server is None:
                raise Abort(
                    dedent(
                        """
                        You must supply the [yellow]license_servers[/yellow] connection strings in the format:
                        [green]license_server_type[/green]:[blue]hostname[/blue]:[magenta]port[/magenta]
                        Use commas to concatenate in case there's more than one entry.
                        """
                    ),
                    subject="Invalid license servers parameter.",
                )

        return license_servers_list
