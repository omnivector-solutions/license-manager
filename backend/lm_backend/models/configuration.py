"""
Database models for configurations table in the License Manager API.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_backend.database import Base


class Configuration(Base):
    """
    Represents the feature configurations.
    """

    __tablename__ = "configs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    grace_time = Column(Integer, CheckConstraint("grace_time>=0"), nullable=False)
    reserved = Column(Integer, CheckConstraint("reserved>=0"), nullable=False)

    cluster = relationship("Cluster", back_populates="configs")

    def __repr__(self):
        return f"Config(id={self.id}, name={self.name}, cluster_id={self.cluster_id}, grace_time={self.grace_time}, reserved={self.reserved})"
