"""add monster link and new action types to combat

Revision ID: 70b7ec424fc2
Revises: 75badec084e0
Create Date: 2026-08-24 21:50:53.698252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70b7ec424fc2'
down_revision: Union[str, Sequence[str], None] = '75badec084e0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NEW_ACTION_TYPES = (
    "attack_weapon",
    "attack_spell",
    "grapple",
    "shove",
    "search",
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "encounter_participants",
        sa.Column("monster_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_encounter_participants_monster_id",
        "encounter_participants",
        "catalog_monsters",
        ["monster_id"],
        ["id"],
    )
    for value in _NEW_ACTION_TYPES:
        op.execute(f"ALTER TYPE combatactiontype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """Downgrade schema.

    Postgres has no `ALTER TYPE ... DROP VALUE` — the new `combatactiontype`
    values added by `upgrade()` are left in place (harmless if unused, same
    limitation `alembic` has everywhere enums grow new values).
    """
    op.drop_constraint(
        "fk_encounter_participants_monster_id",
        "encounter_participants",
        type_="foreignkey",
    )
    op.drop_column("encounter_participants", "monster_id")
