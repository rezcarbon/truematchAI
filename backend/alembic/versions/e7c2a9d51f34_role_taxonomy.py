"""self-learned role taxonomy: role_clusters table + positions.role_cluster_id

Revision ID: e7c2a9d51f34
Revises: d4e1f7a2c9b8
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e7c2a9d51f34"
down_revision = "d4e1f7a2c9b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_clusters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("label", sa.String(length=255), nullable=False, server_default="role family"),
        sa.Column("centroid", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_capabilities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("method", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.add_column(
        "positions",
        sa.Column("role_cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "positions_role_cluster_id_fkey",
        "positions",
        "role_clusters",
        ["role_cluster_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_positions_role_cluster_id", "positions", ["role_cluster_id"])


def downgrade() -> None:
    op.drop_index("ix_positions_role_cluster_id", table_name="positions")
    op.drop_constraint("positions_role_cluster_id_fkey", "positions", type_="foreignkey")
    op.drop_column("positions", "role_cluster_id")
    op.drop_table("role_clusters")
