"""Database model for Bookings."""
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
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity>=0"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    job = relationship("Job", back_populates="bookings", lazy="selectin")
    feature = relationship("Feature", back_populates="bookings", lazy="selectin")

    sortable_fields = [job_id, feature_id]

    def __repr__(self):
        return (
            f"Booking(id={self.id}, "
            f"job_id={self.job_id}, "
            f"feature_id={self.feature_id}, "
            f"quantity={self.quantity}, "
            f"created_at={self.created_at})"
        )
