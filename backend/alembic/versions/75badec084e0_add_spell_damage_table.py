"""add spell damage table

Revision ID: 75badec084e0
Revises: 88a717141b96
Create Date: 2026-08-24 21:45:53.425488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75badec084e0'
down_revision: Union[str, Sequence[str], None] = '88a717141b96'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "catalog_spell_damages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("spell_id", sa.UUID(), nullable=False),
        sa.Column("damage_type_id", sa.UUID(), nullable=False),
        sa.Column(
            "scaling_type",
            sa.Enum("slot_level", "character_level", name="spelldamagescalingtype"),
            nullable=False,
        ),
        sa.Column("scaling_key", sa.Integer(), nullable=False),
        sa.Column("dice_expression", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["damage_type_id"], ["catalog_damage_types.id"]
        ),
        sa.ForeignKeyConstraint(
            ["spell_id"], ["catalog_spells.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "spell_id",
            "scaling_type",
            "scaling_key",
            name="uq_catalog_spell_damages",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("catalog_spell_damages")
    op.execute("DROP TYPE IF EXISTS spelldamagescalingtype")
