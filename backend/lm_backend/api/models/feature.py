"""Database model for Features."""
from sqlalchemy import Column, Integer, SQLColumnExpression, String, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_backend.api.models.booking import Booking
from lm_backend.database import Base


class Feature(Base):
    """
    Represents a feature.
    """

    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    total = Column(Integer, CheckConstraint("total>=0"), default=0, nullable=False)
    used = Column(Integer, CheckConstraint("used>=0"), default=0, nullable=False)
    reserved = Column(Integer, CheckConstraint("reserved>=0"), nullable=False)

    product = relationship("Product", back_populates="features", lazy="selectin")

    bookings = relationship(
        "Booking", back_populates="feature", lazy="selectin", cascade="all, delete-orphan"
    )
    configurations = relationship("Configuration", back_populates="features", lazy="selectin")

    searchable_fields = [name]
    sortable_fields = [name, product_id, config_id, total, used, reserved]

    @hybrid_property
    def booked_total(self) -> int:
        """
        Compute the sum of all bookings.
        """
        return sum(b.quantity for b in self.bookings)

    @booked_total.inplace.expression
    @classmethod
    def _booked_total_expression(cls) -> SQLColumnExpression[int]:
        """
        Provide a sql expression for computing the total bookings for each feature in a subquery.
        """
        return select(func.sum(Booking.quantity)).where(Booking.feature_id == cls.id).label("booked_total")

    def __repr__(self):
        return (
            f"Feature(id={self.id}, "
            f"name={self.name}, "
            f"product_id={self.product_id}, "
            f"config_id={self.config_id}, "
            f"total={self.total}, "
            f"used={self.used}, "
            f"reserved={self.reserved}, "
            f"booked_total={self.booked_total})"
        )
