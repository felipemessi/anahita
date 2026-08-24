"""add character spell slots

Revision ID: d121a5c94acc
Revises: 310c89e4ae01
Create Date: 2026-08-24 20:50:28.976128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd121a5c94acc'
down_revision: Union[str, Sequence[str], None] = '310c89e4ae01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "character_spell_slots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("spell_level", sa.Integer(), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "character_id", "spell_level", name="uq_character_spell_slots"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("character_spell_slots")
