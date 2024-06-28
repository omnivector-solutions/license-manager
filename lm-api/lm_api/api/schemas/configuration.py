"""Configuration schemas for the License Manager API."""
from typing import List, Optional

from pydantic import ConfigDict, BaseModel, Field, PositiveInt

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_api.api.schemas.feature import (
    FeatureSchema,
    FeatureWithOptionalIdUpdateSchema,
    FeatureWithoutConfigIdCreateSchema,
)
from lm_api.api.schemas.license_server import (
    LicenseServerSchema,
    LicenseServerWithOptionalIdUpdateSchema,
    LicenseServerWithoutConfigIdCreateSchema,
)
from lm_api.constants import LicenseServerType


class ConfigurationCreateSchema(BaseCreateSchema):
    """
    Represents the configuration for a set of features.
    """

    name: str = Field(
        ..., title="Name of the configuration", max_length=255, description="The name of the configuration."
    )
    cluster_client_id: str = Field(
        ...,
        title="Client ID of the cluster",
        max_length=255,
        description="The client ID of the cluster that will use this configuration.",
    )
    grace_time: int = Field(
        60,
        gt=0,
        le=2**31 - 1,
        title="Grace time",
        description="The grace time in seconds for the license's bookings to be retained.",
    )

    type: LicenseServerType = Field(
        ...,
        title="Type of license server",
        description="The type of license server that provides the license.",
    )


class ConfigurationCompleteCreateSchema(BaseCreateSchema):
    """
    Represents the data to create a complete configuration.

    Includes the features and the license servers.
    """

    name: str = Field(
        ..., title="Name of the configuration", max_length=255, description="The name of the configuration."
    )
    cluster_client_id: str = Field(
        ...,
        title="Client ID of the cluster",
        max_length=255,
        description="The client ID of the cluster that will use this configuration.",
    )
    grace_time: int = Field(
        60,
        gt=0,
        le=2**31 - 1,
        title="Grace time",
        description="The grace time in seconds for the license's bookings to be retained.",
    )
    type: LicenseServerType = Field(
        ...,
        title="Type of license server",
        description="The type of license server that provides the license.",
    )
    features: List[FeatureWithoutConfigIdCreateSchema] = Field(
        ...,
        title="Features of the configuration",
        description="The features of the configuration.",
    )
    license_servers: List[LicenseServerWithoutConfigIdCreateSchema] = Field(
        ...,
        title="License servers of the configuration",
        description="The license servers of the configuration.",
    )


class ConfigurationUpdateSchema(BaseUpdateSchema):
    """
    Represents the data for a configuration update.
    """

    name: Optional[str] = Field(
        None,
        title="Name of the configuration",
        max_length=255,
        description="The name of the configuration.",
    )
    cluster_client_id: Optional[str] = Field(
        None,
        title="Client ID of the cluster",
        max_length=255,
        description="The client ID of the cluster that will use this configuration.",
    )
    grace_time: Optional[int] = Field(
        None,
        gt=0,
        le=2**31 - 1,
        title="Grace time",
        description="The grace time in seconds for the license's bookings to be retained.",
    )
    type: Optional[LicenseServerType] = Field(
        None,
        title="Type of license server",
        description="The type of license server that provides the license.",
    )


class ConfigurationCompleteUpdateSchema(BaseUpdateSchema):
    """
    Represents the data to update a complete configuration.

    Includes the features and the license servers.
    """

    name: Optional[str] = Field(
        None,
        title="Name of the configuration",
        max_length=255,
        description="The name of the configuration.",
    )
    cluster_client_id: Optional[str] = Field(
        None,
        title="Client ID of the cluster",
        max_length=255,
        description="The client ID of the cluster that will use this configuration.",
    )
    grace_time: Optional[int] = Field(
        None,
        gt=0,
        le=2**31 - 1,
        title="Grace time",
        description="The grace time in seconds for the license's bookings to be retained.",
    )
    type: Optional[LicenseServerType] = Field(
        None,
        title="Type of license server",
        description="The type of license server that provides the license.",
    )
    features: Optional[List[FeatureWithOptionalIdUpdateSchema]] = Field(
        None,
        title="Features of the configuration",
        description="The features of the configuration.",
    )
    license_servers: Optional[List[LicenseServerWithOptionalIdUpdateSchema]] = Field(
        None,
        title="License servers of the configuration",
        description="The license servers of the configuration.",
    )


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int = Field(..., title="ID of the configuration", description="The ID of the configuration.")
    name: str = Field(
        ..., title="Name of the configuration", max_length=255, description="The name of the configuration."
    )
    cluster_client_id: str = Field(
        ...,
        title="Client ID of the cluster",
        max_length=255,
        description="The client ID of the cluster that will use this configuration.",
    )
    features: List[FeatureSchema] = Field(
        ...,
        title="Features of the configuration",
        description="The features of the configuration.",
    )
    license_servers: List[LicenseServerSchema] = Field(
        ...,
        title="License servers of the configuration",
        description="The license servers of the configuration.",
    )
    grace_time: PositiveInt = Field(
        ...,
        title="Grace time",
        description="The grace time in seconds for the license's bookings to be retained.",
    )
    type: LicenseServerType = Field(
        ...,
        title="Type of license server",
        description="The type of license server that provides the license.",
    )
    model_config = ConfigDict(from_attributes=True)
