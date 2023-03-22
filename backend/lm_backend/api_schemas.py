"""
API request and response schemas.
"""
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field


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
    host: str
    port: int
    type: LicenseServerType

    class Config:
        orm_mode = True


class Cluster(BaseModel):
    """
    Represents the clusters in a feature configuration.
    """
    id: Optional[int] = Field(None)
    name: str
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
    name: str
 
    class Config:
        orm_mode = True


class Feature(BaseModel):
    """
    Represents the features in a feature configuration.
    """
    id: Optional[int] = Field(None)
    name: str
    product: Product

    class Config:
        orm_mode = True


class Configuration(BaseModel):
    """
    Represents the configuration for a set of features.
    """
    id: Optional[int] = Field(None)
    name: str
    cluster: Cluster
    license_servers: List[LicenseServer]
    features = List[Feature]
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
