"""add magic/custom items to character equipment

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-31 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_FK_NAME = "fk_character_equipment_magic_item_id_catalog_magic_items"


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        "character_equipment", "item_id", existing_type=sa.UUID(), nullable=True
    )
    op.add_column(
        "character_equipment", sa.Column("magic_item_id", sa.Uuid(), nullable=True)
    )
    op.add_column(
        "character_equipment",
        sa.Column("custom_item_name", sa.String(length=255), nullable=True),
    )
    op.create_foreign_key(
        _FK_NAME,
        "character_equipment",
        "catalog_magic_items",
        ["magic_item_id"],
        ["id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_FK_NAME, "character_equipment", type_="foreignkey")
    op.drop_column("character_equipment", "custom_item_name")
    op.drop_column("character_equipment", "magic_item_id")
    op.alter_column(
        "character_equipment", "item_id", existing_type=sa.UUID(), nullable=False
    )
