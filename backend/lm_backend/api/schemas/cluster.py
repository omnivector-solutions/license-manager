"""Cluster schemas for the License Manager API."""
from typing import List, Optional

from pydantic import BaseModel

from lm_backend.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from lm_backend.api.schemas.configuration import ConfigurationSchema


class ClusterCreateSchema(BaseCreateSchema):
    """
    Clusters to be created in the database.
    """

    name: str
    client_id: str

    class Config:
        orm_mode = True


class ClusterUpdateSchema(BaseUpdateSchema):
    """
    Cluster to be updated in the database.
    """

    name: Optional[str] = None
    client_id: Optional[str] = None


class ClusterSchema(BaseModel):
    """
    Cluster response from the database.
    """

    id: int
    name: str
    client_id: str
    configurations: Optional[List[ConfigurationSchema]] = None

    class Config:
        orm_mode = True
