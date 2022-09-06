"""
Table schema for tables in the license-manager backend
"""
import sqlalchemy
from sqlalchemy import Column, Integer, String, Table, func
from sqlalchemy.sql.schema import CheckConstraint, ForeignKey
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy_utils import ScalarListType  # type: ignore

metadata = sqlalchemy.MetaData()


license_table = Table(
    "license",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product_feature", String, unique=True),
    Column("used", Integer, CheckConstraint("used>=0")),
    Column("total", Integer, CheckConstraint("total>=0")),
    CheckConstraint("used<=total"),
)

license_searchable_fields = [
    license_table.c.product_feature,
]

license_sortable_fields = [
    license_table.c.product_feature,
    license_table.c.used,
    license_table.c.total,
]


booking_table = Table(
    "booking",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("job_id", String),
    Column("product_feature", String),
    Column("booked", Integer, CheckConstraint("booked>=0")),
    Column("lead_host", String),
    Column("user_name", String),
    Column("cluster_name", String),
    Column("created_at", DateTime, default=func.now()),
    Column("config_id", Integer, ForeignKey("config.id"), nullable=False),
)

booking_searchable_fields = [
    booking_table.c.job_id,
    booking_table.c.product_feature,
    booking_table.c.lead_host,
    booking_table.c.user_name,
    booking_table.c.cluster_name,
]

booking_sortable_fields = [
    booking_table.c.job_id,
    booking_table.c.product_feature,
    booking_table.c.booked,
    booking_table.c.lead_host,
    booking_table.c.user_name,
    booking_table.c.cluster_name,
]


config_table = Table(
    "config",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, unique=True),
    Column("product", String),
    Column("features", String),
    Column("license_servers", ScalarListType(str)),
    Column("license_server_type", String),
    Column("grace_time", Integer, CheckConstraint("grace_time>=0")),
    Column("client_id", String, nullable=False, index=True),
)

config_searchable_fields = [
    config_table.c.name,
    config_table.c.product,
    config_table.c.features,
    config_table.c.license_server_type,
    config_table.c.client_id,
]

config_sortable_fields = [
    config_table.c.name,
    config_table.c.product,
    config_table.c.features,
    config_table.c.license_server_type,
    config_table.c.grace_time,
    config_table.c.client_id,
]
