"""remove 'is_active' column

Revision ID: d6d0a6161987
Revises: 9c3d1fb08bb1
Create Date: 2025-02-28 21:39:05.909316

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d6d0a6161987"
down_revision: Union[str, None] = "9c3d1fb08bb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("user", "is_active")


def downgrade() -> None:
    op.add_column(
        "user",
        sa.Column(
            "is_active", sa.BOOLEAN(), autoincrement=False, nullable=False
        ),
    )
