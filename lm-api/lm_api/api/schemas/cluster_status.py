"""Schema definitions for the cluster app."""

from lm_api.api.schemas.base import BaseCreateSchema, BaseUpdateSchema
from pydantic import ConfigDict, field_serializer
from pydantic_extra_types.pendulum_dt import DateTime


class ClusterStatusSchema(BaseCreateSchema, BaseUpdateSchema):
    """
    Represents the data for a cluster status to be created.
    """

    cluster_client_id: str
    interval: int
    last_reported: DateTime
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_serializer("last_reported", when_used="json")
    @classmethod
    def serialize_last_reported(cls, value: DateTime) -> str:
        return value.isoformat().replace("Z", "+00:00")
