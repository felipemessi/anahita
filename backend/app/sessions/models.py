"""SQLAlchemy models for the sessions domain: Session, SessionNote (PRD §7.5)."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.sessions.domain import SessionStatus


class Session(Base):
    """A single game session within a campaign, numbered sequentially."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("campaigns.id"))
    session_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(255))
    scheduled_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[SessionStatus] = mapped_column(
        SAEnum(SessionStatus, name="sessionstatus"), default=SessionStatus.planned
    )
    dm_notes: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    notes: Mapped[list[SessionNote]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class SessionNote(Base):
    """A note attached to a session; private notes are DM-only (PRD §7.5)."""

    __tablename__ = "session_notes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("sessions.id"))
    author_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    session: Mapped[Session] = relationship(back_populates="notes")
