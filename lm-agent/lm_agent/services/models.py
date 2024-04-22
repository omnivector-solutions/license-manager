from pydantic import BaseModel


class ExtractedBookingSchema(BaseModel):
    """
    Represents the booking from a job with the job information extracted.
    """

    booking_id: int
    job_id: int
    slurm_job_id: str
    username: str
    lead_host: str
    feature_id: int
    quantity: int


class ExtractedUsageSchema(BaseModel):
    """
    Representes the usage lines extracted from a feature report.
    """

    feature_id: int
    username: str
    lead_host: str
    quantity: int
