"""Schema definitions for the cluster app."""

from pendulum.datetime import DateTime
from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema


class ClusterStatusSchema(BaseCreateSchema, BaseUpdateSchema):
    """
    Represents the data for a cluster status to be created.
    """

    cluster_client_id: str
    interval: int
    last_reported: DateTime

    class Config:
        orm_mode = True
