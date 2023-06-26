"""Database model for Features."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

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
    reserved = Column(Integer, CheckConstraint("reserved>=0"), nullable=False)

    product = relationship("Product", back_populates="features", lazy="selectin")
    inventory = relationship(
        "Inventory", back_populates="feature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    bookings = relationship(
        "Booking", back_populates="feature", lazy="selectin", cascade="all, delete-orphan"
    )
    configurations = relationship("Configuration", back_populates="features", lazy="selectin")

    searchable_fields = [name]
    sortable_fields = [name, product_id, config_id]

    def __repr__(self):
        return (
            f"Feature(id={self.id}, "
            f"name={self.name}, "
            f"product_id={self.product_id}, "
            f"config_id={self.config_id}, "
            f"reserved={self.reserved})"
        )
