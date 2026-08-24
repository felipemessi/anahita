"""SQLAlchemy models for the wiki domain: WikiPage, WikiPageLink (PRD §7.10)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WikiPage(Base):
    """A free-form, markdown lore page in a campaign, authored by the DM."""

    __tablename__ = "wiki_pages"
    __table_args__ = (
        UniqueConstraint("campaign_id", "slug", name="uq_wiki_page_slug"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[str | None] = mapped_column(String(500))
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    links: Mapped[list[WikiPageLink]] = relationship(
        back_populates="wiki_page", cascade="all, delete-orphan"
    )


class WikiPageLink(Base):
    """A link from a WikiPage to an existing NPC, Location, or Faction.

    `npc_id`, `location_id`, and `faction_id` are mutually exclusive —
    enforced in `app.wiki.domain.validate_wiki_link_kind` — same pattern
    as `LootDrop.item_id`/`magic_item_id`/`custom_item_name` (PRD §7.9).
    """

    __tablename__ = "wiki_page_links"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    wiki_page_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("wiki_pages.id", ondelete="CASCADE")
    )
    npc_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("npcs.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id")
    )
    faction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("factions.id")
    )

    wiki_page: Mapped[WikiPage] = relationship(back_populates="links")
