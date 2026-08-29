"""add catalog race languages

Revision ID: c1d2e3f4a5b6
Revises: 87740a2fcbed
Create Date: 2026-08-29 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: str | Sequence[str] | None = "87740a2fcbed"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "catalog_race_languages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("race_id", sa.UUID(), nullable=False),
        sa.Column("language_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["race_id"], ["catalog_races.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["language_id"], ["catalog_languages.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "race_id", "language_id", name="uq_catalog_race_languages"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("catalog_race_languages")
