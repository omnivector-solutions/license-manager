"""
Database models for bookings table in the License Manager API.
"""
from sqlalchemy import Column, Integer, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from lm_backend.database import Base


class Booking(Base):
    """
    Represents the bookings of a feature.
    """

    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.slurm_id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity>=0"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    job = relationship("Job", back_populates="bookings")

    def __repr__(self):
        return f"Booking(id={self.id}, job_id={self.job_id}, feature_id={self.feature_id}, quantity={self.quantity}, created_at={self.created_at}, config_id={self.config_id})"
