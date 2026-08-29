"""add is_revealed to npcs

Revision ID: d5decfcb2e88
Revises: c1d2e3f4a5b6
Create Date: 2026-08-29 11:32:37.489147

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d5decfcb2e88"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "npcs",
        sa.Column(
            "is_revealed", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
    )
    op.alter_column("npcs", "is_revealed", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("npcs", "is_revealed")
