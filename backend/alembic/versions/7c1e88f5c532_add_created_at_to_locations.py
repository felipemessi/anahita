"""add created_at to locations

Revision ID: 7c1e88f5c532
Revises: 7d0caa036dd1
Create Date: 2026-08-25 13:09:59.585164

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7c1e88f5c532'
down_revision: Union[str, Sequence[str], None] = '7d0caa036dd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "locations",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.alter_column("locations", "created_at", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("locations", "created_at")
