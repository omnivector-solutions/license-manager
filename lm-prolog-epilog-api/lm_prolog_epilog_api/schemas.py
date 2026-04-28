"""Pydantic schemas for request/response models."""

from pydantic import BaseModel


class JobHookRequest(BaseModel):
    """Request body for prolog/epilog endpoints."""

    cluster_name: str
    job_id: str
    lead_host: str
    user_name: str
    job_licenses: str = ""


class JobHookResponse(BaseModel):
    """Response body for prolog/epilog endpoints."""

    status: str
    message: str
