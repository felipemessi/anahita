"""add weapon category to weapon details

Revision ID: 172d0a9e7613
Revises: 476ffda15dd4
Create Date: 2026-08-25 19:58:17.501840

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '172d0a9e7613'
down_revision: Union[str, Sequence[str], None] = '476ffda15dd4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    weapon_category_enum = sa.Enum("simple", "martial", name="weaponcategory")
    weapon_category_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "catalog_weapon_details",
        sa.Column("weapon_category", weapon_category_enum, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("catalog_weapon_details", "weapon_category")
    sa.Enum(name="weaponcategory").drop(op.get_bind(), checkfirst=True)
