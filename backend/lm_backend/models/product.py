"""
Database models for products table in the License Manager API.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from lm_backend.database import Base


class Product(Base):
    """
    Represents a feature's product.
    """

    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    features = relationship("Feature", back_populates="product")

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name})"
