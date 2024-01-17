"""Database model for License Servers."""

from typing import TYPE_CHECKING, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey

from lm_api.api.models.crud_base import CrudBase

if TYPE_CHECKING:
    from lm_api.api.models.configuration import Configuration
else:
    Configuration = "Configuration"


class LicenseServer(CrudBase):
    """
    Represents the license servers in a feature configuration.
    """

    config_id = mapped_column(Integer, ForeignKey("configs.id"), nullable=False)
    host = mapped_column(String, nullable=False)
    port = mapped_column(Integer, CheckConstraint("port>0"), nullable=False)

    configurations: Mapped[List[Configuration]] = relationship(
        Configuration,
        back_populates="license_servers",
        lazy="selectin",
    )

    searchable_fields = [host]
    sortable_fields = [config_id, host]

    def __repr__(self):
        return f"LicenseServer(id={self.id}, host={self.host}, port={self.port})"
