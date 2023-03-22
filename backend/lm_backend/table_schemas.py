"""
Table schema for tables in the License Manager API.
"""

import sqlalchemy
from sqlalchemy import Column, Integer, String, Table, func
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime

metadata = sqlalchemy.MetaData()

license_servers_table = Table(
    "license_servers",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("host", String, nullable=False),
    Column("port", Integer, CheckConstraint("port>=0"), nullable=False),
    Column("type", String, nullable=False),
)

license_servers_searchable_fields = [
    license_servers_table.c.host,
    license_servers_table.c.port,
]

license_servers_sortable_fields = [
    license_servers_table.c.host,
]

clusters_table = Table(
    "clusters",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("client_id", String, nullable=False, unique=True),
)

clusters_searchable_fields = [
    clusters_table.c.name,
    clusters_table.c.client_id,
]

clusters_sortable_fields = [
    clusters_table.c.name,
]

jobs_table = Table(
    "jobs",
    metadata,
    Column("slurm_id", Integer, primary_key=True, autoincrement=False),
    Column("cluster_id", Integer, ForeignKey("clusters.id"), nullable=False),
    Column("username", String, nullable=False),
    Column("lead_host", String, nullable=False),
)

jobs_searchable_fields = [
    jobs_table.c.slurm_id,
]

jobs_sortable_fields = [
    jobs_table.c.slurm_id,
]

configs_table = Table(
    "configs",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("cluster_id", Integer, ForeignKey("clusters.id"), nullable=False),
    Column("grace_time", Integer, CheckConstraint("grace_time>=0"), nullable=False),
    Column("reserved", Integer, CheckConstraint("reserved>=0"), nullable=False),
)

configs_searchable_fields = [
    configs_table.c.name,
]

configs_sortable_fields = [
    configs_table.c.name,
]

license_servers_configs = Table(
    "license_servers_configs_mapping",
    metadata,
    Column("license_server_id", Integer, ForeignKey("license_servers.id"), primary_key=True, nullable=False),
    Column("config_id", Integer, ForeignKey("configs.id"), primary_key=True, nullable=False),
)

products_table = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
)

products_searchable_fields = [
    products_table.c.name,
]

products_sortable_fields = [
    products_table.c.name,
]

features_table = Table(
    "features",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False),
    Column("config_id", Integer, ForeignKey("configs.id"), nullable=False),
)

features_searchable_fields = [
    features_table.c.name,
]

features_sortable_fields = [
    features_table.c.name,
]

inventories_table = Table(
    "inventories",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("feature_id", Integer, ForeignKey("features.id"), nullable=False, unique=True),
    Column("total", Integer, CheckConstraint("total>=0"), nullable=False),
    Column("used", Integer, CheckConstraint("used>=0"), nullable=False),
)

bookings_table = Table(
    "bookings",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", Integer, ForeignKey("jobs.slurm_id"), nullable=False),
    Column("feature_id", Integer, ForeignKey("features.id"), nullable=False),
    Column("quantity", Integer, CheckConstraint("quantity>=0"), nullable=False),
    Column("created_at", DateTime, default=func.now()),
    Column("config_id", Integer, ForeignKey("configs.id"), nullable=False),
)

bookings_searchable_fields = [
    bookings_table.c.job_id,
]

bookings_sortable_fields = [
    bookings_table.c.job_id,
]
