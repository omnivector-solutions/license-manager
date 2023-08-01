"""Database model for Configurations."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint

from lm_backend.database import Base


class Configuration(Base):
    """
    Represents the feature configurations.
    """

    __tablename__ = "configs"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    cluster_client_id = Column(String, nullable=False)
    grace_time = Column(Integer, CheckConstraint("grace_time>=0"), nullable=False)
    type = Column(String, nullable=False)

    license_servers = relationship(
        "LicenseServer", back_populates="configurations", lazy="selectin", cascade="all, delete-orphan"
    )
    features = relationship(
        "Feature", back_populates="configurations", lazy="selectin", cascade="all, delete-orphan"
    )

    searchable_fields = [name]
    sortable_fields = [name, cluster_client_id, type]

    def __repr__(self):
        return (
            f"Config(id={self.id}, "
            f"name={self.name}, "
            f"cluster_client_id={self.cluster_client_id}, "
            f"grace_time={self.grace_time}), "
            f"type={self.type}), "
        )
