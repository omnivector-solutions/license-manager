"""Remove Cluster

Revision ID: 44e596ed28f3
Revises: 82fce3d0720b
Create Date: 2023-07-31 18:28:52.675665

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "44e596ed28f3"
down_revision = "82fce3d0720b"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("configs", sa.Column("cluster_client_id", sa.String(), nullable=True))
    op.execute("UPDATE configs SET cluster_client_id = (SELECT client_id FROM clusters WHERE configs.cluster_id = clusters.id)")
    op.alter_column("configs", "cluster_client_id", nullable=False)
    op.drop_constraint("configs_cluster_id_fkey", "configs", type_="foreignkey")
    op.drop_column("configs", "cluster_id")
    op.add_column("jobs", sa.Column("cluster_client_id", sa.String(), nullable=True))
    op.execute("UPDATE jobs SET cluster_client_id = (SELECT client_id FROM clusters WHERE jobs.cluster_id = clusters.id)")
    op.alter_column("jobs", "cluster_client_id", nullable=False)
    op.drop_constraint("jobs_cluster_id_fkey", "jobs", type_="foreignkey")
    op.drop_column("jobs", "cluster_id")
    op.drop_table("clusters")


def downgrade():
    op.create_table(
        "clusters",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("client_id", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint("id", name="clusters_pkey"),
        sa.UniqueConstraint("client_id", name="clusters_client_id_key"),
        sa.UniqueConstraint("name", name="clusters_name_key"),
    )

    op.execute("INSERT INTO clusters (name, client_id) SELECT DISTINCT cluster_client_id, cluster_client_id FROM configs")
    op.add_column("jobs", sa.Column("cluster_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE jobs SET cluster_id = (SELECT id FROM clusters WHERE jobs.cluster_client_id = clusters.client_id)")
    op.alter_column("jobs", "cluster_id", nullable=False)
    op.create_foreign_key("jobs_cluster_id_fkey", "jobs", "clusters", ["cluster_id"], ["id"])
    op.drop_column("jobs", "cluster_client_id")
    op.add_column("configs", sa.Column("cluster_id", sa.INTEGER(), autoincrement=False, nullable=True))
    op.execute("UPDATE configs SET cluster_id = (SELECT id FROM clusters WHERE configs.cluster_client_id = clusters.client_id)")
    op.alter_column("configs", "cluster_id", nullable=False)
    op.create_foreign_key("configs_cluster_id_fkey", "configs", "clusters", ["cluster_id"], ["id"])
    op.drop_column("configs", "cluster_client_id")
