"""
Database models for features table in the License Manager API.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey

from lm_backend.database import Base


class Feature(Base):
    """
    Represents a feature.
    """

    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)

    product = relationship("Product", back_populates="features")
    inventory = relationship("Inventory", back_populates="feature", uselist=False)

    def __repr__(self):
        return f"Feature(id={self.id}, name={self.name}, product_id={self.product_id}, config_id={self.config_id})"
