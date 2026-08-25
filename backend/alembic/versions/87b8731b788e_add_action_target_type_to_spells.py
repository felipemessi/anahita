"""add action target type to spells

Revision ID: 87b8731b788e
Revises: 81685be0972e
Create Date: 2026-08-25 18:32:26.437977

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87b8731b788e'
down_revision: Union[str, Sequence[str], None] = '81685be0972e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_NAME = "fk_catalog_spells_save_ability_score_id"


def upgrade() -> None:
    """Upgrade schema."""
    action_type_enum = sa.Enum(
        "attack_roll", "saving_throw", "cast_only", name="spellactiontype"
    )
    action_type_enum.create(op.get_bind(), checkfirst=True)
    target_type_enum = sa.Enum(
        "self", "ally", "enemy", "area", "object", name="spelltargettype"
    )
    target_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column("catalog_spells", sa.Column("action_type", action_type_enum, nullable=True))
    op.add_column("catalog_spells", sa.Column("target_type", target_type_enum, nullable=True))
    op.add_column("catalog_spells", sa.Column("save_ability_score_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        _FK_NAME,
        "catalog_spells",
        "catalog_ability_score_definitions",
        ["save_ability_score_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_FK_NAME, "catalog_spells", type_="foreignkey")
    op.drop_column("catalog_spells", "save_ability_score_id")
    op.drop_column("catalog_spells", "target_type")
    op.drop_column("catalog_spells", "action_type")
    sa.Enum(name="spelltargettype").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="spellactiontype").drop(op.get_bind(), checkfirst=True)
