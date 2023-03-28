"""
Schema for features.
"""
from pydantic import BaseModel


class FeatureCreateSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    name: str
    product_id: int


class FeatureUpdateSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    name: str
    product_id: int


class FeatureSchema(BaseModel):
    """
    Represents the features in a feature configuration.
    """

    id: int
    name: str
    product_id: int

    class Config:
        orm_mode = True
