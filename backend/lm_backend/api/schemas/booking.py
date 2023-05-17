"""Booking schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class BookingCreateSchema(BaseCreateSchema):
    """
    Represents the booking of a feature.
    """

    job_id: int
    feature_id: int
    quantity: int


class BookingUpdateSchema(BaseUpdateSchema):
    """
    Represents the booking of a feature.
    """

    job_id: Optional[int] = None
    feature_id: Optional[int] = None
    quantity: Optional[int] = None


class BookingSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int
    job_id: int
    feature_id: int
    quantity: int

    class Config:
        orm_mode = True
