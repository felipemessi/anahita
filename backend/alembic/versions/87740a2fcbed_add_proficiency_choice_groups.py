"""add proficiency choice groups

Revision ID: 87740a2fcbed
Revises: 68f443f24e1a
Create Date: 2026-08-28 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "87740a2fcbed"
down_revision: str | Sequence[str] | None = "68f443f24e1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "catalog_proficiency_choice_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("class_definition_id", sa.UUID(), nullable=True),
        sa.Column("race_id", sa.UUID(), nullable=True),
        sa.Column("choose_count", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "(class_definition_id IS NOT NULL AND race_id IS NULL)"
            " OR (class_definition_id IS NULL AND race_id IS NOT NULL)",
            name="ck_catalog_proficiency_choice_groups_scope",
        ),
        sa.ForeignKeyConstraint(
            ["class_definition_id"],
            ["catalog_class_definitions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["race_id"], ["catalog_races.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "catalog_proficiency_choice_options",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("proficiency_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["catalog_proficiency_choice_groups.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["proficiency_id"], ["catalog_proficiencies.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "group_id",
            "proficiency_id",
            name="uq_catalog_proficiency_choice_options",
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("catalog_proficiency_choice_options")
    op.drop_table("catalog_proficiency_choice_groups")
