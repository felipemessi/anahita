"""add character currency

Revision ID: 9d16defcd13f
Revises: d121a5c94acc
Create Date: 2026-08-24 21:00:05.346953

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9d16defcd13f'
down_revision: Union[str, Sequence[str], None] = 'd121a5c94acc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "characters",
        sa.Column(
            "currency_cp", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
    )
    op.alter_column("characters", "currency_cp", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("characters", "currency_cp")
