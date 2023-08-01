"""Configuration schemas for the License Manager API."""
from typing import List, Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.api.schemas.feature import FeatureSchema
from lm_backend.api.schemas.license_server import LicenseServerSchema
from lm_backend.constants import LicenseServerType


class ConfigurationCreateSchema(BaseCreateSchema):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_client_id: str
    grace_time: int
    type: LicenseServerType


class ConfigurationUpdateSchema(BaseUpdateSchema):
    name: Optional[str] = None
    cluster_client_id: Optional[str] = None
    grace_time: Optional[int] = None
    type: Optional[LicenseServerType] = None


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
