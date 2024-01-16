"""Database model for Products."""

from typing import TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.feature import Feature
else:
    Feature = "Feature"


class Product(CrudBase):
    """
    Represents a feature's product.
    """

    name = mapped_column(String, nullable=False, unique=True)

    features: Mapped[List[Feature]] = relationship(
        Feature,
        back_populates="product",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    searchable_fields = [name]
    sortable_fields = [name]

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name})"
