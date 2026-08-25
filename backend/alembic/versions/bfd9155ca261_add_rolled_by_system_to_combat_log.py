"""add rolled_by_system to combat log

Revision ID: bfd9155ca261
Revises: 70b7ec424fc2
Create Date: 2026-08-24 22:04:47.352268

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bfd9155ca261'
down_revision: Union[str, Sequence[str], None] = '70b7ec424fc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "combat_logs",
        sa.Column(
            "rolled_by_system", sa.Boolean(), nullable=False, server_default=sa.true()
        ),
    )
    op.alter_column("combat_logs", "rolled_by_system", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("combat_logs", "rolled_by_system")
