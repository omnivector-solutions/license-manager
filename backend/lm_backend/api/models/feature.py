"""Database model for Features."""
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_backend.database import Base

if TYPE_CHECKING:
    from lm_backend.api.models.booking import Booking
    from lm_backend.api.models.configuration import Configuration
    from lm_backend.api.models.product import Product
else:
    Booking = "Booking"
    Configuration = "Configuration"
    Product = "Product"


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

    product: Mapped[Product] = relationship(Product, back_populates="features", lazy="selectin")

    bookings: Mapped[List[Booking]] = relationship(
        Booking,
        back_populates="feature",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=True,
    )
    configurations: Mapped[List[Configuration]] = relationship(
        Configuration,
        back_populates="features",
        lazy="selectin",
        uselist=True,
    )

    searchable_fields = [name]
    sortable_fields = [name, product_id, config_id, total, used, reserved]

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
