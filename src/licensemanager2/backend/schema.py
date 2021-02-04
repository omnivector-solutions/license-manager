"""
Table schema for tables in the license-manager backend
"""
import sqlalchemy
from sqlalchemy import Integer, String
from sqlalchemy.sql.schema import CheckConstraint, Column


metadata = sqlalchemy.MetaData()


license_table = sqlalchemy.Table(
    "license",
    metadata,
    Column("product_feature", String, primary_key=True),
    Column("booked", Integer, CheckConstraint("booked>=0")),
    Column("total", Integer, CheckConstraint("total>=0")),
    CheckConstraint("booked<=total"),
)
