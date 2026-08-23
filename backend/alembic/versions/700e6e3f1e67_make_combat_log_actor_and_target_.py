"""make combat log actor and target nullable with set null on delete

Revision ID: 700e6e3f1e67
Revises: 84a905f1c458
Create Date: 2026-08-23 14:39:03.272636

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "700e6e3f1e67"
down_revision: str | Sequence[str] | None = "84a905f1c458"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("combat_logs", "actor_id", existing_type=sa.Uuid(), nullable=True)
    op.drop_constraint(
        "combat_logs_target_id_fkey", "combat_logs", type_="foreignkey"
    )
    op.drop_constraint("combat_logs_actor_id_fkey", "combat_logs", type_="foreignkey")
    op.create_foreign_key(
        "combat_logs_target_id_fkey",
        "combat_logs",
        "encounter_participants",
        ["target_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "combat_logs_actor_id_fkey",
        "combat_logs",
        "encounter_participants",
        ["actor_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "combat_logs_target_id_fkey", "combat_logs", type_="foreignkey"
    )
    op.drop_constraint("combat_logs_actor_id_fkey", "combat_logs", type_="foreignkey")
    op.create_foreign_key(
        "combat_logs_actor_id_fkey",
        "combat_logs",
        "encounter_participants",
        ["actor_id"],
        ["id"],
    )
    op.create_foreign_key(
        "combat_logs_target_id_fkey",
        "combat_logs",
        "encounter_participants",
        ["target_id"],
        ["id"],
    )
    op.alter_column("combat_logs", "actor_id", existing_type=sa.Uuid(), nullable=False)
