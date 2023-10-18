"""Database model for Bookings."""
from typing import TYPE_CHECKING

from sqlalchemy import Column, Integer, func
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from lm_backend.database import Base

if TYPE_CHECKING:
    from lm_backend.api.models.feature import Feature
    from lm_backend.api.models.job import Job
else:
    Feature = "Feature"
    Job = "Job"


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

    job: Mapped[Job] = relationship(Job, back_populates="bookings", lazy="selectin")
    feature: Mapped[Feature] = relationship(Feature, back_populates="bookings", lazy="selectin")

    sortable_fields = [job_id, feature_id]

    def __repr__(self):
        return (
            f"Booking(id={self.id}, "
            f"job_id={self.job_id}, "
            f"feature_id={self.feature_id}, "
            f"quantity={self.quantity}, "
            f"created_at={self.created_at})"
        )
