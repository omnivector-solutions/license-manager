"""
Database models for license_servers table in the License Manager API.
"""
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.schema import CheckConstraint

from lm_backend.database import Base


class LicenseServer(Base):
    """
    Represents the license servers in a feature configuration.
    """

    __tablename__ = "license_servers"
    id = Column(Integer, primary_key=True)
    host = Column(String, nullable=False)
    port = Column(Integer, CheckConstraint("port>0"), nullable=False)
    type = Column(String, nullable=False)

    def __repr__(self):
        return f"LicenseServer(id={self.id}, host={self.host}, port={self.port}, type={self.type})"
