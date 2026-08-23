"""Pydantic request/response schemas for the sessions domain."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.sessions.domain import SessionStatus


class SessionCreate(BaseModel):
    """Request body to create a session. `session_number` is assigned server-side."""

    title: str = Field(min_length=1, max_length=255)
    scheduled_date: date | None = None
    summary: str | None = None
    dm_notes: str | None = None


class SessionRead(BaseModel):
    """Response schema for a session.

    `dm_notes` is only populated for the campaign's DM — `None` otherwise,
    regardless of whether the session actually has DM notes (PRD §7.5: DM
    notes are private).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    session_number: int
    title: str
    scheduled_date: date | None
    status: SessionStatus
    dm_notes: str | None
    summary: str | None
    created_at: datetime


class SessionNoteCreate(BaseModel):
    """Request body to add a note to a session."""

    content: str = Field(min_length=1)
    is_private: bool = False


class SessionNoteRead(BaseModel):
    """Response schema for a session note."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    author_id: uuid.UUID
    content: str
    is_private: bool
    created_at: datetime
