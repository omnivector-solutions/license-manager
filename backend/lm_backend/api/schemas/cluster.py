"""
Schemas for clusters.
"""
from pydantic import BaseModel


class Cluster(BaseModel):
    """
    Represents the clusters in a feature configuration.
    """

    class ClusterCreateSchema(BaseModel):
        """
        Represents the clusters in a feature configuration.
        """

        name: str
        client_id: str

    class ClusterUpdateSchema(BaseModel):
        """
        Represents the clusters in a feature configuration.
        """

        name: str
        client_id: str

    class ClusterSchema(BaseModel):
        id: int
        name: str
        client_id: str

    class Config:
        orm_mode = True
