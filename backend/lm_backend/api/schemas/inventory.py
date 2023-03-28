"""Schemas for inventories."""
from pydantic import BaseModel


class InventoryCreateSchema(BaseModel):
    """
    Represents the inventory of a feature.
    """

    feature_id: int
    total: int
    used: int
    booked: int
    available: int


class InventoryUpdateSchema(BaseModel):
    """
    Represents the inventory of a feature.
    """

    feature_id: int
    total: int
    used: int
    booked: int
    available: int


class InventorySchema(BaseModel):
    """
    Represents the inventory of a feature.
    """

    id: int
    feature_id: int
    total: int
    used: int
    booked: int
    available: int

    class Config:
        orm_mode = True
