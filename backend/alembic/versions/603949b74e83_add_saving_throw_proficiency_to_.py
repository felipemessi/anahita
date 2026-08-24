"""add saving throw proficiency to character ability scores

Revision ID: 603949b74e83
Revises: 0fd12fb5b2ae
Create Date: 2026-08-24 19:46:35.176577

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '603949b74e83'
down_revision: Union[str, Sequence[str], None] = '0fd12fb5b2ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "character_ability_scores",
        sa.Column(
            "save_proficient",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("character_ability_scores", "save_proficient", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("character_ability_scores", "save_proficient")
