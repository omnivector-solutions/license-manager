"""
Table schema for tables in the license-manager backend
"""
import sqlalchemy
from sqlalchemy import Integer, String
from sqlalchemy.sql.schema import CheckConstraint, Column

from sqlalchemy_utils import ScalarListType  # type: ignore


metadata = sqlalchemy.MetaData()


license_table = sqlalchemy.Table(
    "license",
    metadata,
    Column("product_feature", String, primary_key=True),
    Column("used", Integer, CheckConstraint("used>=0")),
    Column("total", Integer, CheckConstraint("total>=0")),
    CheckConstraint("used<=total"),
)


booking_table = sqlalchemy.Table(
    "booking",
    metadata,
    Column("job_id", String, primary_key=True),
    Column("product_feature", String, primary_key=True),
    Column("booked", Integer, CheckConstraint("booked>=0")),
)

config_table = sqlalchemy.Table(
    "config",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("product", String),
    Column("features", ScalarListType(str)),
    Column("license_servers", ScalarListType(str)),
    Column("license_server_type", String),
    Column("grace_time", Integer, CheckConstraint("grace_time>=0")),
)
