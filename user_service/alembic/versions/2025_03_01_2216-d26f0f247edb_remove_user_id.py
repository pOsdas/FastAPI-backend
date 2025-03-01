"""remove user_id

Revision ID: d26f0f247edb
Revises: b5a8aa43bbad
Create Date: 2025-03-01 22:16:03.100883

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d26f0f247edb"
down_revision: Union[str, None] = "b5a8aa43bbad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user", sa.Column("is_active", sa.Boolean(), nullable=False))
    op.drop_column("user", "user_id")


def downgrade() -> None:
    op.add_column(
        "user",
        sa.Column("user_id", sa.INTEGER(), autoincrement=True, nullable=False),
    )
    op.drop_column("user", "is_active")
