"""add campaigns domain

Revision ID: 8045f11d1dfb
Revises: 6f9cf284365a
Create Date: 2026-08-23 01:47:14.325153

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8045f11d1dfb"
down_revision: str | Sequence[str] | None = "6f9cf284365a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("setting", sa.String(length=255), nullable=True),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "paused", "archived", name="campaignstatus"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "campaign_invites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("invite_code", sa.String(length=64), nullable=False),
        sa.Column("role", sa.Enum("dm", "player", name="campaignrole"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["used_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code"),
    )
    op.create_table(
        "campaign_members",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Enum("dm", "player", name="campaignrole"), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "campaign_id", "user_id", name="uq_campaign_members_campaign_user"
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("campaign_members")
    op.drop_table("campaign_invites")
    op.drop_table("campaigns")
    # Enum types are independent of the tables that use them in Postgres and
    # survive `DROP TABLE` — drop them explicitly so upgrade/downgrade/upgrade
    # cycles stay repeatable.
    op.execute("DROP TYPE IF EXISTS campaignrole")
    op.execute("DROP TYPE IF EXISTS campaignstatus")
