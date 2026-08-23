"""SQLAlchemy models for campaigns domain: Campaign, CampaignMember, CampaignInvite."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.campaigns.domain import CampaignRole, CampaignStatus
from app.database import Base

# Shared instance so the `campaignrole` Postgres enum type is only ever
# declared once, even though it backs columns on two different tables.
_campaign_role_enum = SAEnum(CampaignRole, name="campaignrole")


class Campaign(Base):
    """A D&D 5e campaign owned by a user."""

    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    setting: Mapped[str | None] = mapped_column(String(255))
    owner_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    status: Mapped[CampaignStatus] = mapped_column(
        SAEnum(CampaignStatus, name="campaignstatus"),
        default=CampaignStatus.active,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    members: Mapped[list[CampaignMember]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )
    invites: Mapped[list[CampaignInvite]] = relationship(
        back_populates="campaign", cascade="all, delete-orphan"
    )


class CampaignMember(Base):
    """A user's membership in a campaign, with their role."""

    __tablename__ = "campaign_members"
    __table_args__ = (
        UniqueConstraint(
            "campaign_id", "user_id", name="uq_campaign_members_campaign_user"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    role: Mapped[CampaignRole] = mapped_column(_campaign_role_enum)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    campaign: Mapped[Campaign] = relationship(back_populates="members")


class CampaignInvite(Base):
    """A single-use invite code granting a role in a campaign."""

    __tablename__ = "campaign_invites"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    invite_code: Mapped[str] = mapped_column(String(64), unique=True)
    role: Mapped[CampaignRole] = mapped_column(_campaign_role_enum)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    campaign: Mapped[Campaign] = relationship(back_populates="invites")
