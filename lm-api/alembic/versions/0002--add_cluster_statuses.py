"""Add cluster statuses endpoint

Revision ID: 6dc00c5c3e40
Revises: 594b52f2c088
Create Date: 2024-05-20 11:23:59.160338

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6dc00c5c3e40'
down_revision = '594b52f2c088'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "cluster_statuses",
        sa.Column("cluster_client_id", sa.String(), nullable=False),
        sa.Column("interval", sa.Integer(), nullable=False),
        sa.Column("last_reported", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("cluster_client_id"),
    )


def downgrade():
    op.drop_table("cluster_statuses")
