"""add fields 'user_id' and 'is_active'

Revision ID: b5a8aa43bbad
Revises: d6d0a6161987
Create Date: 2025-03-01 00:25:20.673637

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b5a8aa43bbad"
down_revision: Union[str, None] = "d6d0a6161987"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("user_id", sa.Integer(), nullable=False))
    op.add_column("user", sa.Column("is_active", sa.Boolean(), nullable=False))


def downgrade() -> None:
    op.drop_column("user", "is_active")
    op.drop_column("user", "user_id")
