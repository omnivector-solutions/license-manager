"""
Schemas for jobs.
"""
from pydantic import BaseModel


class JobCreateSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_id: int
    cluster_id: int
    username: str
    lead_host: str


class JobUpdateSchema(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_id: int
    cluster_id: int
    username: str
    lead_host: str


class Job(BaseModel):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_id: int
    cluster_id: int
    username: str
    lead_host: str

    class Config:
        orm_mode = True
