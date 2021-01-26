"""
Table schema for tables in the license-manager backend
"""
import sqlalchemy


metadata = sqlalchemy.MetaData()


license_table = sqlalchemy.Table(
    "license",
    metadata,
    sqlalchemy.Column("product_feature", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column("booked", sqlalchemy.Integer),
    sqlalchemy.Column("total", sqlalchemy.Integer),
)
