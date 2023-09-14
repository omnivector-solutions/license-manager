"""Configuration schemas for the License Manager API."""
from typing import List, Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.api.schemas.feature import (
    FeatureSchema,
    FeatureWithOptionalIdUpdateSchema,
    FeatureWithoutConfigIdCreateSchema,
)
from lm_backend.api.schemas.license_server import (
    LicenseServerSchema,
    LicenseServerWithOptionalIdUpdateSchema,
    LicenseServerWithoutConfigIdCreateSchema,
)
from lm_backend.constants import LicenseServerType


class ConfigurationCreateSchema(BaseCreateSchema):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_client_id: str
    grace_time: int
    type: LicenseServerType


class ConfigurationCompleteCreateSchema(BaseCreateSchema):
    """
    Represents the data to create a complete configuration.

    Includes the features and the license servers.
    """

    name: str
    cluster_client_id: str
    grace_time: int
    type: LicenseServerType
    features: List[FeatureWithoutConfigIdCreateSchema] = []
    license_servers: List[LicenseServerWithoutConfigIdCreateSchema] = []


class ConfigurationUpdateSchema(BaseUpdateSchema):
    """
    Represents the data for a configuration update.
    """

    name: Optional[str] = None
    cluster_client_id: Optional[str] = None
    grace_time: Optional[int] = None
    type: Optional[LicenseServerType] = None


class ConfigurationCompleteUpdateSchema(BaseUpdateSchema):
    """
    Represents the data to update a complete configuration.

    Includes the features and the license servers.
    """

    name: Optional[str] = None
    cluster_client_id: Optional[str] = None
    grace_time: Optional[int] = None
    type: Optional[LicenseServerType] = None
    features: Optional[List[FeatureWithOptionalIdUpdateSchema]] = None
    license_servers: Optional[List[LicenseServerWithOptionalIdUpdateSchema]] = None


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_client_id: str
    features: List[FeatureSchema] = []
    license_servers: List[LicenseServerSchema] = []
    grace_time: int
    type: LicenseServerType

    class Config:
        orm_mode = True
