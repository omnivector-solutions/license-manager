"""Booking schemas for the License Manager API."""
from typing import Optional

from pydantic import BaseModel, Field, PositiveInt

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class BookingCreateSchema(BaseCreateSchema):
    """
    Represents the booking of a feature.
    """

    job_id: int = Field(..., title="Job ID", description="The ID of the job that booked the feature.")
    feature_id: int = Field(..., title="Feature ID", description="The ID of the feature that was booked.")
    quantity: PositiveInt = Field(
        ..., title="Quantity", description="The quantity of the feature that was booked."
    )


class BookingUpdateSchema(BaseUpdateSchema):
    """
    Represents the booking of a feature.
    """

    job_id: Optional[int] = Field(
        None, title="Job ID", description="The ID of the job that booked the feature."
    )
    feature_id: Optional[int] = Field(
        None, title="Feature ID", description="The ID of the feature that was booked."
    )
    quantity: Optional[PositiveInt] = Field(
        None, title="Quantity", description="The quantity of the feature that was booked."
    )


class BookingSchema(BaseModel):
    """
    Represents the booking of a feature.
    """

    id: int = Field(..., title="ID", description="The ID of the booking.")
    job_id: int = Field(..., title="Job ID", description="The ID of the job that booked the feature.")
    feature_id: int = Field(..., title="Feature ID", description="The ID of the feature that was booked.")
    quantity: PositiveInt = Field(
        ..., title="Quantity", description="The quantity of the feature that was booked."
    )

    class Config:
        orm_mode = True
