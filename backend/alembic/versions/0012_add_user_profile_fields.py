"""Add location and headline fields to users table.

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-03 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0012'
down_revision = '0011'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add location column
    op.add_column('users', sa.Column('location', sa.String(255), nullable=True))
    # Add headline column
    op.add_column('users', sa.Column('headline', sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'headline')
    op.drop_column('users', 'location')
