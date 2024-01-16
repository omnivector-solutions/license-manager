"""Database model for Features."""
from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.booking import Booking
    from lm_api.api.models.configuration import Configuration
    from lm_api.api.models.product import Product
else:
    Booking = "Booking"
    Configuration = "Configuration"
    Product = "Product"


class Feature(CrudBase):
    """
    Represents a feature.
    """

    name = mapped_column(String, nullable=False)
    product_id = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    config_id = mapped_column(Integer, ForeignKey("configs.id"), nullable=False)
    total = mapped_column(Integer, CheckConstraint("total>=0"), default=0, nullable=False)
    used = mapped_column(Integer, CheckConstraint("used>=0"), default=0, nullable=False)
    reserved = mapped_column(Integer, CheckConstraint("reserved>=0"), nullable=False)

    product = relationship(Product, back_populates="features", lazy="selectin")

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
            f"reserved={self.reserved})"
        )
