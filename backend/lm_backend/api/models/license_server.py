"""Database model for License Servers."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_backend.database import Base

if TYPE_CHECKING:
    from lm_backend.api.models.configuration import Configuration
else:
    Configuration = "Configuration"


class LicenseServer(Base):
    """
    Represents the license servers in a feature configuration.
    """

    __tablename__ = "license_servers"
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, CheckConstraint("port>0"), nullable=False)

    configurations: Mapped[List[Configuration]] = relationship(
        Configuration,
        back_populates="license_servers",
        lazy="selectin",
    )

    searchable_fields = [host]
    sortable_fields = [config_id, host]

    def __repr__(self):
        return f"LicenseServer(id={self.id}, host={self.host}, port={self.port})"
