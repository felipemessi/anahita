"""add combat domain

Revision ID: 84a905f1c458
Revises: 5faf7b3b9560
Create Date: 2026-08-23 13:22:45.849465

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "84a905f1c458"
down_revision: str | Sequence[str] | None = "5faf7b3b9560"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "encounters",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("preparing", "active", "completed", name="encounterstatus"),
            nullable=False,
        ),
        sa.Column("current_round", sa.Integer(), nullable=False),
        sa.Column("current_turn_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "encounter_participants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=False),
        sa.Column("character_id", sa.Uuid(), nullable=True),
        sa.Column("npc_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("initiative", sa.Integer(), nullable=False),
        sa.Column("hit_point_max", sa.Integer(), nullable=False),
        sa.Column("hit_point_current", sa.Integer(), nullable=False),
        sa.Column("temporary_hit_points", sa.Integer(), nullable=False),
        sa.Column("armor_class", sa.Integer(), nullable=False),
        sa.Column("turn_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["character_id"], ["characters.id"]),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "combat_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("encounter_id", sa.Uuid(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("turn_order", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column(
            "action_type",
            sa.Enum(
                "attack",
                "spell",
                "move",
                "dash",
                "dodge",
                "disengage",
                "help",
                "hide",
                "ready",
                "other",
                name="combatactiontype",
            ),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("damage_dealt", sa.Integer(), nullable=True),
        sa.Column("damage_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_id"], ["encounter_participants.id"]),
        sa.ForeignKeyConstraint(["encounter_id"], ["encounters.id"]),
        sa.ForeignKeyConstraint(["target_id"], ["encounter_participants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "encounter_conditions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("participant_id", sa.Uuid(), nullable=False),
        sa.Column(
            "condition",
            sa.Enum(
                "blinded",
                "charmed",
                "deafened",
                "exhaustion",
                "frightened",
                "grappled",
                "incapacitated",
                "invisible",
                "paralyzed",
                "petrified",
                "poisoned",
                "prone",
                "restrained",
                "stunned",
                "unconscious",
                name="combatconditiontype",
            ),
            nullable=False,
        ),
        sa.Column("duration_rounds", sa.Integer(), nullable=True),
        sa.Column("applied_at_round", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["participant_id"], ["encounter_participants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("encounter_conditions")
    op.drop_table("combat_logs")
    op.drop_table("encounter_participants")
    op.drop_table("encounters")
    # DROP TABLE doesn't remove Postgres enum types — drop them explicitly
    # (same pattern as the campaigns domain migration).
    sa.Enum(name="combatconditiontype").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="combatactiontype").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="encounterstatus").drop(op.get_bind(), checkfirst=False)
