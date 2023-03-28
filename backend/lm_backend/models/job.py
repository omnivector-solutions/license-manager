"""
Database models for jobs table in the License Manager API.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from lm_backend.database import Base


class Job(Base):
    """
    Represents the jobs submitted in a cluster.
    """

    __tablename__ = "jobs"
    slurm_id = Column(Integer, primary_key=True, autoincrement=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    username = Column(String, nullable=False)
    lead_host = Column(String, nullable=False)

    bookings = relationship("Booking", back_populates="job")
    cluster = relationship("Cluster", back_populates="jobs")

    def __repr__(self):
        return f"Job(slurm_id={self.slurm_id}, cluster_id={self.cluster_id}, username={self.username}, lead_host={self.lead_host})"
