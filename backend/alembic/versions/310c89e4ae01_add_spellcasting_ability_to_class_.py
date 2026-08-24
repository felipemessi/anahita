"""add spellcasting_ability to class_definitions

Revision ID: 310c89e4ae01
Revises: 603949b74e83
Create Date: 2026-08-24 20:33:22.560507

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '310c89e4ae01'
down_revision: Union[str, Sequence[str], None] = '603949b74e83'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "catalog_class_definitions",
        sa.Column("spellcasting_ability", sa.String(length=3), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("catalog_class_definitions", "spellcasting_ability")
