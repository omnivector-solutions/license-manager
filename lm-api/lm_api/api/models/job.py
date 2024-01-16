"""Database model for Jobs."""

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.booking import Booking
else:
    Booking = "Booking"


class Job(CrudBase):
    """
    Represents the jobs submitted in a cluster.
    """

    slurm_job_id = mapped_column(String, nullable=False)
    cluster_client_id = mapped_column(String, nullable=False)
    username = mapped_column(String, nullable=False)
    lead_host = mapped_column(String, nullable=False)

    bookings: Mapped[List[Booking]] = relationship(
        Booking,
        back_populates="job",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    searchable_fields = [slurm_job_id, username, lead_host]
    sortable_fields = [slurm_job_id, cluster_client_id, username, lead_host]

    def __repr__(self):
        return (
            f"Job(id={self.id}, "
            f"slurm_job_id={self.slurm_job_id}, "
            f"cluster_client_id={self.cluster_client_id}, "
            f"username={self.username}, "
            f"lead_host={self.lead_host})"
        )
