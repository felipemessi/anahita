"""add character concentration duration

Revision ID: a1b2c3d4e5f6
Revises: d5decfcb2e88
Create Date: 2026-08-30 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "d5decfcb2e88"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FK_NAME = "fk_characters_concentration_encounter_id_encounters"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "characters",
        sa.Column("concentration_encounter_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "characters",
        sa.Column("concentration_round_started", sa.Integer(), nullable=True),
    )
    op.add_column(
        "characters",
        sa.Column("concentration_duration_rounds", sa.Integer(), nullable=True),
    )
    op.add_column(
        "characters",
        sa.Column(
            "concentration_expires_at", sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_foreign_key(
        _FK_NAME, "characters", "encounters", ["concentration_encounter_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_FK_NAME, "characters", type_="foreignkey")
    op.drop_column("characters", "concentration_expires_at")
    op.drop_column("characters", "concentration_duration_rounds")
    op.drop_column("characters", "concentration_round_started")
    op.drop_column("characters", "concentration_encounter_id")
