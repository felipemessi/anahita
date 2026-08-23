"""add characters domain

Revision ID: 8b62d1294f95
Revises: 8045f11d1dfb
Create Date: 2026-08-23 02:05:23.834405

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8b62d1294f95"
down_revision: str | Sequence[str] | None = "8045f11d1dfb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "characters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_member_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("race_id", sa.UUID(), nullable=False),
        sa.Column("subrace_id", sa.UUID(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("experience_points", sa.Integer(), nullable=False),
        sa.Column("alignment", sa.String(length=100), nullable=True),
        sa.Column("background", sa.String(length=255), nullable=True),
        sa.Column("hit_point_max", sa.Integer(), nullable=False),
        sa.Column("hit_point_current", sa.Integer(), nullable=False),
        sa.Column("temporary_hit_points", sa.Integer(), nullable=False),
        sa.Column("armor_class", sa.Integer(), nullable=False),
        sa.Column("speed", sa.Integer(), nullable=False),
        sa.Column("inspiration", sa.Boolean(), nullable=False),
        sa.Column("proficiency_bonus", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["campaign_member_id"], ["campaign_members.id"]),
        sa.ForeignKeyConstraint(["race_id"], ["catalog_races.id"]),
        sa.ForeignKeyConstraint(["subrace_id"], ["catalog_subraces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_ability_scores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column(
            "ability",
            sa.Enum(
                "str",
                "dex",
                "con",
                "int",
                "wis",
                "cha",
                name="characterabilityscoreability",
            ),
            nullable=False,
        ),
        sa.Column("base_score", sa.Integer(), nullable=False),
        sa.Column("asi_bonus", sa.Integer(), nullable=False),
        sa.Column("misc_bonus", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_classes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("class_definition_id", sa.UUID(), nullable=False),
        sa.Column("subclass_id", sa.UUID(), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(
            ["class_definition_id"], ["catalog_class_definitions.id"]
        ),
        sa.ForeignKeyConstraint(
            ["subclass_id"], ["catalog_subclass_definitions.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_equipment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("item_id", sa.UUID(), nullable=False),
        sa.Column("equipped", sa.Boolean(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("attunement", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["catalog_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_features",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column(
            "source_type",
            sa.Enum("class_", "feat", name="characterfeaturesourcetype"),
            nullable=False,
        ),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("level_acquired", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_race_choices",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("race_trait_id", sa.UUID(), nullable=False),
        sa.Column("chosen_value", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["race_trait_id"], ["catalog_race_traits.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_skills",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column(
            "skill",
            sa.Enum(
                "acrobatics",
                "animal_handling",
                "arcana",
                "athletics",
                "deception",
                "history",
                "insight",
                "intimidation",
                "investigation",
                "medicine",
                "nature",
                "perception",
                "performance",
                "persuasion",
                "religion",
                "sleight_of_hand",
                "stealth",
                "survival",
                name="characterskill",
            ),
            nullable=False,
        ),
        sa.Column("proficient", sa.Boolean(), nullable=False),
        sa.Column("expertise", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "character_spells",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=False),
        sa.Column("spell_id", sa.UUID(), nullable=False),
        sa.Column("prepared", sa.Boolean(), nullable=False),
        sa.Column("source_class", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["spell_id"], ["catalog_spells.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("character_spells")
    op.drop_table("character_skills")
    op.drop_table("character_race_choices")
    op.drop_table("character_features")
    op.drop_table("character_equipment")
    op.drop_table("character_classes")
    op.drop_table("character_ability_scores")
    op.drop_table("characters")
    # Enum types are independent of the tables that use them in Postgres and
    # survive `DROP TABLE` — drop them explicitly so upgrade/downgrade/upgrade
    # cycles stay repeatable.
    op.execute("DROP TYPE IF EXISTS characterabilityscoreability")
    op.execute("DROP TYPE IF EXISTS characterfeaturesourcetype")
    op.execute("DROP TYPE IF EXISTS characterskill")
