"""add character portrait key

Revision ID: 68f443f24e1a
Revises: 54374794b595
Create Date: 2026-08-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68f443f24e1a"
down_revision: str | Sequence[str] | None = "54374794b595"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "characters", sa.Column("portrait_key", sa.String(length=500), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("characters", "portrait_key")
