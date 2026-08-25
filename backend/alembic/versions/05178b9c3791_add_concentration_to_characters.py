"""add_concentration_to_characters

Revision ID: 05178b9c3791
Revises: 05e55ada520e
Create Date: 2026-08-25 09:45:59.595752

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05178b9c3791'
down_revision: Union[str, Sequence[str], None] = '05e55ada520e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_FK_NAME = "fk_characters_concentrating_spell_id_catalog_spells"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'characters', sa.Column('concentrating_spell_id', sa.Uuid(), nullable=True)
    )
    op.create_foreign_key(
        _FK_NAME, 'characters', 'catalog_spells', ['concentrating_spell_id'], ['id']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_FK_NAME, 'characters', type_='foreignkey')
    op.drop_column('characters', 'concentrating_spell_id')
