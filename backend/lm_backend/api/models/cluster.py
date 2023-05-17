"""Database model for Clusters."""
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from lm_backend.database import Base


class Cluster(Base):
    """
    Represents the clusters in a feature configuration.
    """

    __tablename__ = "clusters"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    client_id = Column(String, nullable=False, unique=True)

    configurations = relationship(
        "Configuration", back_populates="cluster", lazy="selectin", cascade="all, delete-orphan"
    )

    searchable_fields = [name, client_id]
    sortable_fields = [name, client_id]

    def __repr__(self):
        return f"Cluster(id={self.id}, name={self.name}, client_id={self.client_id})"
