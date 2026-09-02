"""add session maps and map tokens

Revision ID: ca33fc4cedbf
Revises: b2c3d4e5f6a7
Create Date: 2026-09-01 23:20:02.026437

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ca33fc4cedbf"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENCOUNTER_MAP_FK = "fk_encounters_map_id_session_maps"


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "session_maps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=500), nullable=False),
        sa.Column("width_px", sa.Integer(), nullable=False),
        sa.Column("height_px", sa.Integer(), nullable=False),
        sa.Column("grid_size_px", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "map_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("map_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=True),
        sa.Column("npc_id", sa.Uuid(), nullable=True),
        sa.Column("monster_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("is_visible", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["map_id"], ["session_maps.id"]),
        sa.ForeignKeyConstraint(["monster_id"], ["catalog_monsters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("encounters", sa.Column("map_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        _ENCOUNTER_MAP_FK, "encounters", "session_maps", ["map_id"], ["id"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(_ENCOUNTER_MAP_FK, "encounters", type_="foreignkey")
    op.drop_column("encounters", "map_id")
    op.drop_table("map_tokens")
    op.drop_table("session_maps")
