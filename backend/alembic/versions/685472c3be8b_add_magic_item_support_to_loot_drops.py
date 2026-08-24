"""add magic item support to loot drops

Revision ID: 685472c3be8b
Revises: eff39325d01b
Create Date: 2026-08-23 23:58:52.959600

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "685472c3be8b"
down_revision: str | Sequence[str] | None = "eff39325d01b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FK_NAME = "fk_loot_drops_magic_item_id_catalog_magic_items"


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("loot_drops", sa.Column("magic_item_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        _FK_NAME, "loot_drops", "catalog_magic_items", ["magic_item_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_FK_NAME, "loot_drops", type_="foreignkey")
    op.drop_column("loot_drops", "magic_item_id")
