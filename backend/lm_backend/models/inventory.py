"""
Database models for inventories in the License Manager API.
"""
from sqlalchemy import Column, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_backend.database import Base


class Inventory(Base):
    """
    Represents the inventory of a feature.
    """

    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, unique=True)
    total = Column(Integer, CheckConstraint("total>=0"), nullable=False)
    used = Column(Integer, CheckConstraint("used>=0"), nullable=False)

    feature = relationship("Feature", back_populates="inventory")

    def __repr__(self):
        return f"Inventory(id={self.id}, feature_id={self.feature_id}, total={self.total}, used={self.used})"
