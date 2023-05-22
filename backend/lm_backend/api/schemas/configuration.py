"""Configuration schemas for the License Manager API."""
from typing import List, Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.api.schemas.feature import FeatureSchema
from lm_backend.api.schemas.license_server import LicenseServerSchema


class ConfigurationCreateSchema(BaseCreateSchema):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_id: int
    grace_time: int


class ConfigurationUpdateSchema(BaseUpdateSchema):
    name: Optional[str] = None
    cluster_id: Optional[int] = None
    grace_time: Optional[int] = None


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_id: int
    features: List[FeatureSchema] = []
    license_servers: List[LicenseServerSchema] = []
    grace_time: int

    class Config:
        orm_mode = True
