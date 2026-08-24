"""Pydantic request/response schemas for the timeline domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TimelineEventCreate(BaseModel):
    """Request body to create a manual timeline event."""

    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    session_id: uuid.UUID | None = None
    in_game_date: str | None = None
    sort_order: int


class TimelineEventUpdate(BaseModel):
    """Request body to update a manual timeline event. Omitted fields unchanged."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    session_id: uuid.UUID | None = None
    in_game_date: str | None = None
    sort_order: int | None = None


class TimelineEventRead(BaseModel):
    """Response schema for a manual timeline event."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    title: str
    description: str | None
    session_id: uuid.UUID | None
    in_game_date: str | None
    sort_order: int
    created_at: datetime


class TimelineEntryRead(BaseModel):
    """Response schema for one fused timeline entry — automatic or manual."""

    entry_type: str
    id: uuid.UUID
    title: str
    description: str | None
    session_id: uuid.UUID | None
    in_game_date: str | None
    sort_order: int
    created_at: datetime
