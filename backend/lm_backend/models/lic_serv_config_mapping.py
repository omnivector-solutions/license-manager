"""
Database models for lic_serv_config_mapping in the License Manager API.
"""
from sqlalchemy import Column, Integer
from sqlalchemy.sql.schema import ForeignKey

from lm_backend.database import Base


class LicServConfigMapping(Base):
    """
    Represents the many-to-many relationship between license servers and configs.
    """

    __tablename__ = "license_servers_configs_mapping"
    license_server_id = Column(Integer, ForeignKey("license_servers.id"), primary_key=True, nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), primary_key=True, nullable=False)

    def __repr__(self):
        return f"license_servers_configs_mapping(license_server_id={self.license_server_id}, config_id={self.config_id})"
