"""SQLAlchemy models for the handouts domain (PRD §7.8)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.handouts.domain import HandoutType


class Handout(Base):
    """A piece of shareable content (text/image/map) a DM reveals to players.

    `session_id` is nullable — a handout can be general to the campaign
    rather than tied to a specific session (PRD §7.8). `storage_key` is an
    abstract reference resolved to a URL by `StorageService`; binary content
    is never stored in the database.
    """

    __tablename__ = "handouts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sessions.id")
    )
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str | None] = mapped_column(Text)
    handout_type: Mapped[HandoutType] = mapped_column(
        SAEnum(HandoutType, name="handouttype")
    )
    storage_key: Mapped[str | None] = mapped_column(String(500))
    is_revealed: Mapped[bool] = mapped_column(Boolean, default=False)
    revealed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
