"""merge production-blockers (0014) into mainline (0023)

Revision ID: 84d7f25bb018
Revises: 0014, 0023
Create Date: 2026-06-13 03:40:44.903681
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84d7f25bb018'
down_revision: Union[str, None] = ('0014', '0023')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
