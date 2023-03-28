"""API schemas for cluster endpoints."""
from pydantic import BaseModel


class ClusterCreateRequest(BaseModel):
    """
    Cluster to be created in the database.
    """
    name: str
    client_id: str

    class Config:
        orm_mode = True


class ClusterResponse(BaseModel):
    """
    Cluster response from the backend.
    """
    id: int
    name: str
    client_id: str

    class Config:
        orm_mode = True
