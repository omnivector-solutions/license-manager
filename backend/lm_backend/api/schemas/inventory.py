"""Inventory schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class InventoryCreateSchema(BaseCreateSchema):
    """
    Represents the inventory of a feature.
    """

    feature_id: int
    total: int
    used: int


class InventoryUpdateSchema(BaseUpdateSchema):
    """
    Represents the inventory of a feature.
    """

    feature_id: Optional[int] = None
    total: Optional[int] = None
    used: Optional[int] = None


class InventorySchema(BaseModel):
    """
    Represents the inventory of a feature.
    """

    id: int
    feature_id: int
    total: int
    used: int

    class Config:
        orm_mode = True
