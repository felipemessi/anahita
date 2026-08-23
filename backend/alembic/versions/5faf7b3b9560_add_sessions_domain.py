"""add sessions domain

Revision ID: 5faf7b3b9560
Revises: 8b62d1294f95
Create Date: 2026-08-23 02:30:59.640200

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5faf7b3b9560"
down_revision: str | Sequence[str] | None = "8b62d1294f95"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("session_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("scheduled_date", sa.Date(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("planned", "in_progress", "completed", name="sessionstatus"),
            nullable=False,
        ),
        sa.Column("dm_notes", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "session_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("author_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("is_private", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("session_notes")
    op.drop_table("sessions")
    # Enum types are independent of the tables that use them in Postgres and
    # survive `DROP TABLE` — drop them explicitly so upgrade/downgrade/upgrade
    # cycles stay repeatable.
    op.execute("DROP TYPE IF EXISTS sessionstatus")
