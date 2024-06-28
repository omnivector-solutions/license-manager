"""Job schemas for the License Manager API."""
from typing import List, Optional

from pydantic import ConfigDict, BaseModel, Field

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_api.api.schemas.booking import BookingSchema


class JobBookingCreateSchema(BaseCreateSchema):
    product_feature: str = Field(
        ..., title="Product feature", description="The product.feature of the license."
    )
    quantity: int = Field(
        ..., gt=0, le=2**31 - 1, title="Quantity", description="The quantity of booked licenses."
    )


class JobCreateSchema(BaseCreateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: str = Field(..., title="Slurm job ID", description="The ID of the job in the cluster.")
    cluster_client_id: str = Field(
        ...,
        title="Client ID of the cluster",
        description="The client ID of the cluster that submitted the job.",
    )
    username: str = Field(
        ..., title="Username", description="The username of the user that submitted the job."
    )
    lead_host: str = Field(
        ..., title="Lead host", description="The lead host of the cluster that submitted the job."
    )


class JobWithBookingCreateSchema(BaseCreateSchema):
    """
    Represents the jobs submitted in a cluster with its bookings.
    """

    slurm_job_id: str = Field(..., title="Slurm job ID", description="The ID of the job in the cluster.")
    cluster_client_id: Optional[str] = Field(
        None,
        title="Client ID of the cluster",
        description="The client ID of the cluster that submitted the job.",
    )
    username: str = Field(
        ..., title="Username", description="The username of the user that submitted the job."
    )
    lead_host: str = Field(
        ..., title="Lead host", description="The lead host of the cluster that submitted the job."
    )
    bookings: List[JobBookingCreateSchema] = Field(
        ..., title="Bookings", description="The bookings of the job."
    )


class JobUpdateSchema(BaseUpdateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: Optional[str] = Field(
        None, title="Slurm job ID", description="The ID of the job in the cluster."
    )
    cluster_client_id: Optional[str] = Field(
        None,
        title="Client ID of the cluster",
        description="The client ID of the cluster that submitted the job.",
    )
    username: Optional[str] = Field(
        None, title="Username", description="The username of the user that submitted the job."
    )
    lead_host: Optional[str] = Field(
        None, title="Lead host", description="The lead host of the cluster that submitted the job."
    )


class JobSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    id: int = Field(..., title="ID", description="The ID of the job.")
    slurm_job_id: str = Field(..., title="Slurm job ID", description="The ID of the job in the cluster.")
    cluster_client_id: str = Field(
        ...,
        title="Client ID of the cluster",
        description="The client ID of the cluster that submitted the job.",
    )
    username: str = Field(
        ..., title="Username", description="The username of the user that submitted the job."
    )
    lead_host: str = Field(
        ..., title="Lead host", description="The lead host of the cluster that submitted the job."
    )

    bookings: Optional[List[BookingSchema]] = Field(
        None, title="Bookings", description="The bookings of the job."
    )
    model_config = ConfigDict(from_attributes=True)
