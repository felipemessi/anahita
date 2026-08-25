"""make participant initiative nullable and add session open

Revision ID: 88a717141b96
Revises: 9d16defcd13f
Create Date: 2026-08-24 21:09:28.011132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '88a717141b96'
down_revision: Union[str, Sequence[str], None] = '9d16defcd13f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "encounter_participants", "initiative", existing_type=sa.Integer(), nullable=True
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "encounter_participants", "initiative", existing_type=sa.Integer(), nullable=False
    )
