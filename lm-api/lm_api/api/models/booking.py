"""Database model for Bookings."""
from typing import TYPE_CHECKING

from sqlalchemy import Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.feature import Feature
    from lm_api.api.models.job import Job
else:
    Feature = "Feature"
    Job = "Job"


class Booking(CrudBase):
    """
    Represents the bookings of a feature.
    """

    job_id = mapped_column(Integer, ForeignKey("jobs.id"), nullable=False)
    feature_id = mapped_column(Integer, ForeignKey("features.id"), nullable=False)
    quantity = mapped_column(Integer, CheckConstraint("quantity>=0"), nullable=False)
    created_at = mapped_column(DateTime, default=func.now())

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
