"""Database model for Products."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship

from lm_backend.database import Base

if TYPE_CHECKING:
    from lm_backend.api.models.feature import Feature
else:
    Feature = "Feature"


class Product(Base):
    """
    Represents a feature's product.
    """

    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

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
