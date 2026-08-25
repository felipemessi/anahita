"""add armor category to armor details

Revision ID: 476ffda15dd4
Revises: 87b8731b788e
Create Date: 2026-08-25 18:58:56.416855

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '476ffda15dd4'
down_revision: Union[str, Sequence[str], None] = '87b8731b788e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    armor_category_enum = sa.Enum(
        "light", "medium", "heavy", "shield", name="armorcategory"
    )
    armor_category_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "catalog_armor_details",
        sa.Column("armor_category", armor_category_enum, nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("catalog_armor_details", "armor_category")
    sa.Enum(name="armorcategory").drop(op.get_bind(), checkfirst=True)
