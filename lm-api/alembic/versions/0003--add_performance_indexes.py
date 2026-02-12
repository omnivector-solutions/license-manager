"""Add performance indexes for metrics queries

Revision ID: a1b2c3d4e5f6
Revises: 6dc00c5c3e40
Create Date: 2026-02-12 02:15:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = '6dc00c5c3e40'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add indexes to optimize the metrics collection query and other common queries.

    The metrics query joins Configuration, Feature, and Product tables.
    Adding indexes on foreign key columns and frequently queried fields
    will significantly improve query performance, especially as data grows.

    Additional indexes are added for bookings and jobs to optimize queries
    that filter or join on these tables.
    """
    # Index on features.config_id for join with configurations
    op.create_index("idx_features_config_id", "features", ["config_id"], unique=False)

    # Index on features.product_id for join with products
    op.create_index("idx_features_product_id", "features", ["product_id"], unique=False)

    # Composite index on features for common query patterns
    # This covers the metrics query which filters/joins by config_id and product_id
    op.create_index("idx_features_config_product", "features", ["config_id", "product_id"], unique=False)

    # Index on configurations.cluster_client_id for filtering by cluster
    op.create_index("idx_configs_cluster_client_id", "configs", ["cluster_client_id"], unique=False)

    # Index on bookings.job_id for join with jobs
    op.create_index("idx_bookings_job_id", "bookings", ["job_id"], unique=False)

    # Index on bookings.feature_id for join with features
    op.create_index("idx_bookings_feature_id", "bookings", ["feature_id"], unique=False)

    # Index on jobs.cluster_client_id for filtering by cluster
    op.create_index("idx_jobs_cluster_client_id", "jobs", ["cluster_client_id"], unique=False)

    # Index on jobs.slurm_job_id for lookup by job ID
    op.create_index("idx_jobs_slurm_job_id", "jobs", ["slurm_job_id"], unique=False)


def downgrade():
    """
    Remove performance indexes.
    """
    op.drop_index("idx_jobs_slurm_job_id", table_name="jobs")
    op.drop_index("idx_jobs_cluster_client_id", table_name="jobs")
    op.drop_index("idx_bookings_feature_id", table_name="bookings")
    op.drop_index("idx_bookings_job_id", table_name="bookings")
    op.drop_index("idx_configs_cluster_client_id", table_name="configs")
    op.drop_index("idx_features_config_product", table_name="features")
    op.drop_index("idx_features_product_id", table_name="features")
    op.drop_index("idx_features_config_id", table_name="features")
