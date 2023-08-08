"""Database model for Jobs."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from lm_backend.database import Base


class Job(Base):
    """
    Represents the jobs submitted in a cluster.
    """

    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    slurm_job_id = Column(String, nullable=False)
    cluster_client_id = Column(String, nullable=False)
    username = Column(String, nullable=False)
    lead_host = Column(String, nullable=False)

    bookings = relationship("Booking", back_populates="job", lazy="selectin", cascade="all, delete-orphan")

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
