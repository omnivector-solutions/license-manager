"""
Database models for the database tables in the License Manager API.
Tables:
    - license_servers
    - clusters
    - configs
    - products
    - features
    - inventory
    - jobs
    - bookings
"""
from sqlalchemy import Column, Integer, String, func
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

from lm_backend.database import Base


class LicenseServer(Base):
    """
    Represents the license servers in a feature configuration.
    """

    __tablename__ = "license_servers"
    id = Column(Integer, primary_key=True)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, CheckConstraint("port>0"), nullable=False)
    type = Column(String, nullable=False)

    configurations = relationship("Configuration", back_populates="license_servers", lazy="selectin")

    searchable_fields = [type, host]
    sortable_fields = [config_id, type, host]

    def __repr__(self):
        return f"LicenseServer(id={self.id}, host={self.host}, port={self.port}, type={self.type})"


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
            f"grace_time={self.grace_time}"
        )


class Product(Base):
    """
    Represents a feature's product.
    """

    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    features = relationship(
        "Feature", back_populates="product", lazy="selectin", cascade="all, delete-orphan"
    )

    searchable_fields = [name]
    sortable_fields = [name]

    def __repr__(self):
        return f"Product(id={self.id}, name={self.name})"


class Feature(Base):
    """
    Represents a feature.
    """

    __tablename__ = "features"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    reserved = Column(Integer, CheckConstraint("reserved>=0"), nullable=False)

    product = relationship("Product", back_populates="features", lazy="selectin")
    inventory = relationship(
        "Inventory", back_populates="feature", uselist=False, lazy="selectin", cascade="all, delete-orphan"
    )
    bookings = relationship(
        "Booking", back_populates="feature", lazy="selectin", cascade="all, delete-orphan"
    )
    configurations = relationship("Configuration", back_populates="features", lazy="selectin")

    searchable_fields = [name]
    sortable_fields = [name, product_id, config_id]

    def __repr__(self):
        return (
            f"Feature(id={self.id}, "
            f"name={self.name}, "
            f"product_id={self.product_id}, "
            f"config_id={self.config_id}), "
            f"reserved={self.reserved}"
        )


class Inventory(Base):
    """
    Represents the inventory of a feature.
    """

    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False, unique=True)
    total = Column(Integer, CheckConstraint("total>=0"), nullable=False)
    used = Column(Integer, CheckConstraint("used>=0"), nullable=False)

    feature = relationship("Feature", back_populates="inventory", lazy="selectin")

    def __repr__(self):
        return f"Inventory(id={self.id}, feature_id={self.feature_id}, total={self.total}, used={self.used})"


class Job(Base):
    """
    Represents the jobs submitted in a cluster.
    """

    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    slurm_job_id = Column(String, nullable=False)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False)
    username = Column(String, nullable=False)
    lead_host = Column(String, nullable=False)

    bookings = relationship("Booking", back_populates="job", lazy="selectin", cascade="all, delete-orphan")

    searchable_fields = [slurm_job_id, username, lead_host]
    sortable_fields = [slurm_job_id, cluster_id, username, lead_host]

    def __repr__(self):
        return (
            f"Job(id={self.id}, "
            f"slurm_job_id={self.slurm_job_id}, "
            f"cluster_id={self.cluster_id}, "
            f"username={self.username}, "
            f"lead_host={self.lead_host})"
        )


class Booking(Base):
    """
    Represents the bookings of a feature.
    """

    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    feature_id = Column(Integer, ForeignKey("features.id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity>=0"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    job = relationship("Job", back_populates="bookings", lazy="selectin")
    feature = relationship("Feature", back_populates="bookings", lazy="selectin")

    sortable_fields = [job_id, feature_id]

    def __repr__(self):
        return (
            f"Booking(id={self.id}, "
            f"job_id={self.job_id}, "
            f"feature_id={self.feature_id}, "
            f"quantity={self.quantity}, "
            f"created_at={self.created_at}"
        )