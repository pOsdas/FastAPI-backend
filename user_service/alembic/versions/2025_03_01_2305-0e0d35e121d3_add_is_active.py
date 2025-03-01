"""add is_active

Revision ID: 0e0d35e121d3
Revises: d26f0f247edb
Create Date: 2025-03-01 23:05:59.034471

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0e0d35e121d3"
down_revision: Union[str, None] = "d26f0f247edb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("is_active", sa.Boolean(), nullable=False))


def downgrade() -> None:
    op.drop_column("user", "is_active")
