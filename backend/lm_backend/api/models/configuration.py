"""Database model for Configurations."""
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

    cluster = relationship("Cluster", back_populates="configurations", lazy="selectin")
    license_servers = relationship(
        "LicenseServer", back_populates="configurations", lazy="selectin", cascade="all, delete-orphan"
    )
    features = relationship(
        "Feature", back_populates="configurations", lazy="selectin", cascade="all, delete-orphan"
    )

    searchable_fields = [name]
    sortable_fields = [name, cluster_id]

    def __repr__(self):
        return (
            f"Config(id={self.id}, "
            f"name={self.name}, "
            f"cluster_id={self.cluster_id}, "
            f"grace_time={self.grace_time})"
        )
