"""SQLAlchemy models for world-building: NPC, Location, Faction (PRD §7.7)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.world.domain import (
    FactionRelationshipType,
    LocationType,
    NPCLocationPresenceType,
)


class NPC(Base):
    """A non-player character in a campaign, with an optional stat block.

    `stat_block_id` points at `catalog_monsters` — either an SRD monster or a
    campaign homebrew (same `is_custom`/`campaign_id` scoping as the rest of
    the catalog). An NPC with no stat block is purely narrative.
    """

    __tablename__ = "npcs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    name: Mapped[str] = mapped_column(String(255))
    race: Mapped[str] = mapped_column(String(100))
    occupation: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    personality: Mapped[str | None] = mapped_column(Text)
    is_alive: Mapped[bool] = mapped_column(Boolean, default=True)
    stat_block_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("catalog_monsters.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )


class Location(Base):
    """A place in a campaign's world, optionally nested under a parent location."""

    __tablename__ = "locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    name: Mapped[str] = mapped_column(String(255))
    location_type: Mapped[LocationType] = mapped_column(
        SAEnum(LocationType, name="locationtype")
    )
    description: Mapped[str] = mapped_column(Text)
    parent_location_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("locations.id")
    )


class Faction(Base):
    """An organization or group within a campaign."""

    __tablename__ = "factions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    alignment: Mapped[str | None] = mapped_column(String(100))
    influence_level: Mapped[str | None] = mapped_column(String(100))


class NPCFaction(Base):
    """Junction: an NPC's role within a Faction."""

    __tablename__ = "npc_factions"
    __table_args__ = (UniqueConstraint("npc_id", "faction_id", name="uq_npc_factions"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    npc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("npcs.id", ondelete="CASCADE")
    )
    faction_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factions.id", ondelete="CASCADE")
    )
    role_in_faction: Mapped[str | None] = mapped_column(String(255))


class NPCLocation(Base):
    """Junction: how an NPC is present at a Location."""

    __tablename__ = "npc_locations"
    __table_args__ = (
        UniqueConstraint("npc_id", "location_id", name="uq_npc_locations"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    npc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("npcs.id", ondelete="CASCADE")
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="CASCADE")
    )
    presence_type: Mapped[NPCLocationPresenceType] = mapped_column(
        SAEnum(NPCLocationPresenceType, name="npclocationpresencetype")
    )


class NPCSession(Base):
    """Junction: an NPC's appearance in a Session."""

    __tablename__ = "npc_sessions"
    __table_args__ = (UniqueConstraint("npc_id", "session_id", name="uq_npc_sessions"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    npc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("npcs.id", ondelete="CASCADE")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id", ondelete="CASCADE")
    )
    appearance_note: Mapped[str | None] = mapped_column(Text)


class LocationSession(Base):
    """Junction: a Location visited during a Session."""

    __tablename__ = "location_sessions"
    __table_args__ = (
        UniqueConstraint("location_id", "session_id", name="uq_location_sessions"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("locations.id", ondelete="CASCADE")
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("sessions.id", ondelete="CASCADE")
    )
    visit_note: Mapped[str | None] = mapped_column(Text)


class FactionRelationship(Base):
    """Junction: the relationship between two Factions."""

    __tablename__ = "faction_relationships"
    __table_args__ = (
        UniqueConstraint(
            "faction_a_id", "faction_b_id", name="uq_faction_relationships"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    faction_a_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factions.id", ondelete="CASCADE")
    )
    faction_b_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("factions.id", ondelete="CASCADE")
    )
    relationship_type: Mapped[FactionRelationshipType] = mapped_column(
        SAEnum(FactionRelationshipType, name="factionrelationshiptype")
    )
