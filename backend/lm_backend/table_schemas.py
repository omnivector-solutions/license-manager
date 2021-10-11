"""
Table schema for tables in the license-manager backend
"""
import datetime

import sqlalchemy
from sqlalchemy import Column, Integer, String, Table
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
    Column("created_at", DateTime, default=datetime.datetime.utcnow),
    Column("config_id", Integer, ForeignKey("config.id"), nullable=False),
)


config_table = Table(
    "config",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product", String),
    Column("features", String),
    Column("license_servers", ScalarListType(str)),
    Column("license_server_type", String),
    Column("grace_time", Integer, CheckConstraint("grace_time>=0")),
)
