"""SQLAlchemy models for the timeline domain: TimelineEvent (PRD §7.10).

Only manually-created events are persisted here. The automatic entries —
one per session with a `summary` — are computed on read from `Session`
(see `app.queries.timeline_queries`), never stored, so there is no
duplicated data to keep in sync.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TimelineEvent(Base):
    """A DM-authored, manually-placed event on a campaign's timeline."""

    __tablename__ = "timeline_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("sessions.id")
    )
    in_game_date: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
