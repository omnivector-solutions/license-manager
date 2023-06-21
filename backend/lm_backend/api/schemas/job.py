"""Job schemas for the License Manager API."""
from typing import List, Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.api.schemas.booking import BookingSchema


class JobBookingCreateSchema(BaseCreateSchema):
    feature_id: int
    quantity: int


class JobCreateSchema(BaseCreateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: str
    cluster_id: int
    username: str
    lead_host: str
    bookings: List[JobBookingCreateSchema] = []


class JobUpdateSchema(BaseUpdateSchema):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id: Optional[str]
    cluster_id: Optional[int]
    username: Optional[str]
    lead_host: Optional[str]


class JobSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    id: int
    slurm_job_id: str
    cluster_id: int
    username: str
    lead_host: str

    bookings: Optional[List[BookingSchema]] = None

    class Config:
        orm_mode = True
