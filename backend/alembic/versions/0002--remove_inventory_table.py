"""Remove Inventory

Revision ID: 82fce3d0720b
Revises: 594b52f2c088
Create Date: 2023-07-31 17:52:42.749565

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "82fce3d0720b"
down_revision = "594b52f2c088"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("inventories")
    op.add_column("features", sa.Column("total", sa.Integer(), nullable=True))
    op.add_column("features", sa.Column("used", sa.Integer(), nullable=True))
    op.execute("UPDATE features SET total = 0, used = 0")
    op.alter_column("features", "total", nullable=False)
    op.alter_column("features", "used", nullable=False)


def downgrade():
    op.drop_column("features", "used")
    op.drop_column("features", "total")
    op.create_table(
        "inventories",
        sa.Column("id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("feature_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.Column("total", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.Column("used", sa.INTEGER(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(["feature_id"], ["features.id"], name="features"),
        sa.PrimaryKeyConstraint("id", name="inventories_pkey"),
    )
