"""SQLAlchemy models for the maps domain: SessionMap, MapToken (backlog Fase 15)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SessionMap(Base):
    """A battle map image uploaded for a session, with a 5ft grid overlay.

    `storage_key` is resolved to a URL by `StorageService`, same convention
    as `app.handouts.models.Handout` — binary image data is never stored in
    the database. `width_px`/`height_px` (the uploaded image's pixel size)
    and `grid_size_px` (how many pixels one 5ft cell spans) are supplied by
    the uploading client — this app has no server-side image inspection
    (no Pillow dependency), so the DM's client is trusted to report them
    accurately when overlaying the grid.
    """

    __tablename__ = "session_maps"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sessions.id"))
    name: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(500))
    width_px: Mapped[int] = mapped_column(Integer)
    height_px: Mapped[int] = mapped_column(Integer)
    grid_size_px: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    tokens: Mapped[list[MapToken]] = relationship(
        back_populates="map", cascade="all, delete-orphan"
    )


class MapToken(Base):
    """A positionable marker on a `SessionMap`, linked to a PC/NPC/monster.

    `character_id`/`npc_id`/`monster_id` are mutually exclusive (never more
    than one set) — enforced in `app.maps.domain.validate_token_kind`, same
    pattern as `app.combat.models.EncounterParticipant`. `x`/`y` are grid
    cell coordinates (not pixels) — the frontend multiplies by
    `SessionMap.grid_size_px` to place it in the image.
    """

    __tablename__ = "map_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    map_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("session_maps.id"))
    character_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("characters.id")
    )
    # FK to a future/existing `npcs.id` — omitted at the DB level, same
    # documented choice as `EncounterParticipant.npc_id`.
    npc_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    monster_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("catalog_monsters.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(255))
    x: Mapped[int] = mapped_column(Integer)
    y: Mapped[int] = mapped_column(Integer)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    map: Mapped[SessionMap] = relationship(back_populates="tokens")
