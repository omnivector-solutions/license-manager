"""
API request and response schemas.
"""
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field

from lm_backend.constants import LicenseServerType


class LicenseServerType(str, Enum):
    """
    Describe the supported license server types that may be used for fetching licenses from license servers.
    """

    FLEXLM = "flexlm"
    RLM = "rlm"
    LMX = "lmx"
    LSDYNA = "lsdyna"
    OLICENSE = "olicense"
    

class LicenseServer(BaseModel):
    """
    Represents the license servers in a feature configuration.
    """
    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    product: str
    features: str
    license_servers: List[str]
    license_server_type: LicenseServerType
    grace_time: int
    client_id: str

    class Config:
        orm_mode = True


class Job(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """
    slurm_id: int
    cluster: Cluster
    username: str
    lead_host: str

    class Config:
        orm_mode = True


class Product(BaseModel):
    """
    Represents a feature's product.
    """
    id: Optional[int] = Field(None)
    name: Optional[str] = Field(None)
    product: str
    features: dict
    license_servers: List[str]
    license_server_type: LicenseServerType
    grace_time: int

    class Config:
        orm_mode = True


class Inventory(BaseModel):
    """
    Represents the inventory of a feature.
    """
    id: Optional[int] = Field(None)
    feature: Feature
    total: int
    used: int
    booked: int
    available: int

    class Config:
        orm_mode = True
