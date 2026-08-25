"""add_legendary_action_reaction_tracking_and_action_types

Revision ID: 62a1ec4d1e1f
Revises: 05178b9c3791
Create Date: 2026-08-25 09:57:57.648975

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62a1ec4d1e1f'
down_revision: Union[str, Sequence[str], None] = '05178b9c3791'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_ACTION_TYPES = ("legendary_action", "reaction")


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'encounter_participants',
        sa.Column(
            'legendary_actions_used', sa.Integer(), nullable=False, server_default='0'
        ),
    )
    op.add_column(
        'encounter_participants',
        sa.Column('reactions_used', sa.Integer(), nullable=False, server_default='0'),
    )
    for value in _NEW_ACTION_TYPES:
        op.execute(f"ALTER TYPE combatactiontype ADD VALUE IF NOT EXISTS '{value}'")


def downgrade() -> None:
    """Downgrade schema.

    Postgres has no `ALTER TYPE ... DROP VALUE` — the new `combatactiontype`
    values added by `upgrade()` are left in place, same limitation noted in
    `70b7ec424fc2_add_monster_link_and_new_action_types_.py`.
    """
    op.drop_column('encounter_participants', 'reactions_used')
    op.drop_column('encounter_participants', 'legendary_actions_used')
