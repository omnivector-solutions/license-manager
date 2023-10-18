"""Database model for Configurations."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.schema import CheckConstraint

from lm_backend.database import Base

if TYPE_CHECKING:
    from lm_backend.api.models.feature import Feature
    from lm_backend.api.models.license_server import LicenseServer
else:
    Feature = "Feature"
    LicenseServer = "LicenseServer"


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

    license_servers: Mapped[List[LicenseServer]] = relationship(
        LicenseServer,
        back_populates="configurations",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=True,
    )
    features: Mapped[List[Feature]] = relationship(
        Feature,
        back_populates="configurations",
        lazy="selectin",
        cascade="all, delete-orphan",
        uselist=True,
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
