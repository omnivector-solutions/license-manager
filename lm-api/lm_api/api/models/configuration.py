"""Database model for Configurations."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.sql.schema import CheckConstraint

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.feature import Feature
    from lm_api.api.models.license_server import LicenseServer
else:
    Feature = "Feature"
    LicenseServer = "LicenseServer"


class Configuration(CrudBase):
    """
    Represents the feature configurations.
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return "configs"

    name = mapped_column(String, nullable=False)
    cluster_client_id = mapped_column(String, nullable=False)
    grace_time = mapped_column(Integer, CheckConstraint("grace_time>=0"), nullable=False)
    type = mapped_column(String, nullable=False)

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
