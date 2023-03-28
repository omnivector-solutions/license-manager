"""
Schemas for configurations.
"""
from pydantic import BaseModel


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
