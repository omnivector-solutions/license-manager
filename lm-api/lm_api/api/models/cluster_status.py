"""Database models for the cluster health resource."""

from pendulum.datetime import DateTime as PendulumDateTime
from sqlalchemy import DateTime, Integer, String
from lm_api.api.models.crud_base import CrudWithoutId

from inflection import tableize
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class ClusterStatus(CrudWithoutId):
    """Cluster status table definition."""

    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        """
        Dynamically create table name based on the class name.
        """
        return tableize(cls.__name__)

    cluster_client_id: Mapped[str] = mapped_column(String, primary_key=True)
    interval: Mapped[int] = mapped_column(Integer, nullable=False)
    last_reported: Mapped[PendulumDateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=PendulumDateTime.utcnow,
    )

    @property
    def is_healthy(self) -> bool:
        """Return True if the last_reported time is before now plus the interval in seconds between pings."""
        return PendulumDateTime.utcnow().subtract(seconds=self.interval) <= self.last_reported
