"""
Pydantic models for various data items.
"""
from typing import Optional

import httpx
from pydantic import BaseModel, Extra, PositiveInt

from lm_cli.constants import LicenseServerType


class TokenSet(BaseModel, extra=Extra.ignore):
    """
    A model representing a pairing of access and refresh tokens.
    """

    access_token: str
    refresh_token: Optional[str] = None


class Persona(BaseModel):
    """
    A model representing a pairing of a TokenSet and Identity data.

    This is a convenience to combine all of the identifying data and credentials for a given user.
    """

    token_set: TokenSet
    user_email: str


class DeviceCodeData(BaseModel, extra=Extra.ignore):
    """
    A model representing the data that is returned from OIDC's device code endpoint.
    """

    device_code: str
    verification_uri_complete: str
    interval: int


class LicenseManagerContext(BaseModel, arbitrary_types_allowed=True):
    """
    A data object describing context passed from the main entry point.
    """

    persona: Optional[Persona]
    client: Optional[httpx.Client]


class LicenseServerCreateSchema(BaseModel):
    """
    License server response from the database.
    """

    config_id: int
    host: str
    port: PositiveInt


class ProductCreateSchema(BaseModel):
    """
    Represents a feature's product.
    """

    name: str


class FeatureCreateSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    name: str
    product_id: int
    config_id: int
    reserved: int


class ConfigurationCreateSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_client_id: str
    grace_time: int
    type: LicenseServerType
