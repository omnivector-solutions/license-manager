"""
Schemas for clusters and configurations.
"""
from typing import Optional, List

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class ConfigurationCreateSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    name: str
    cluster_id: int
    grace_time: int


class ConfigurationUpdateSchema(BaseModel):
    name: str
    cluster_id: int
    grace_time: int


class ConfigurationSchema(BaseModel):
    """
    Represents the configuration for a set of features.
    """

    id: int
    name: str
    cluster_id: int
    grace_time: int

    class Config:
        orm_mode = True


class ClusterCreateSchema(BaseCreateSchema):
    """
    Clusters to be created in the database.
    """

    name: str
    client_id: str
    configurations: List[ConfigurationSchema] = None

    class Config:
        orm_mode = True


class ClusterUpdateSchema(BaseUpdateSchema):
    """
    Cluster to be updated in the database.
    """

    name: Optional[str] = None
    client_id: Optional[str] = None
    configurations: Optional[List[ConfigurationSchema]] = None


class ClusterSchema(BaseModel):
    """
    Cluster response from the database.
    """

    id: int
    name: str
    client_id: str
    configurations: List[ConfigurationSchema] = None

    class Config:
        orm_mode = True
