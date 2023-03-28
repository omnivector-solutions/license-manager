"""
Schemas for bookings.
"""
from pydantic import BaseModel


class BookingCreateSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    job_id: int
    feature_id: int
    config_id: int
    quantity: int


class BookingUpdateSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    job_id: int
    feature_id: int
    config_id: int
    quantity: int


class BookingSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int
    job_id: int
    feature_id: int
    config_id: int
    quantity: int

    class Config:
        orm_mode = True
