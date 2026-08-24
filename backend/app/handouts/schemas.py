"""Pydantic request/response schemas for the handouts domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.handouts.domain import HandoutType


class HandoutCreate(BaseModel):
    """Form fields to create a handout (the file itself is a separate upload part)."""

    title: str = Field(min_length=1, max_length=255)
    handout_type: HandoutType
    content: str | None = None
    session_id: uuid.UUID | None = None


class HandoutRead(BaseModel):
    """Response schema for a handout, with its file resolved to a URL."""

    model_config = ConfigDict(from_attributes=False)

    id: uuid.UUID
    campaign_id: uuid.UUID
    session_id: uuid.UUID | None
    title: str
    content: str | None
    handout_type: HandoutType
    url: str | None
    is_revealed: bool
    revealed_at: datetime | None
    created_at: datetime


class HandoutRevealedEvent(BaseModel):
    """Payload broadcast over the combat WebSocket (PRD §10.3)."""

    id: uuid.UUID
    title: str
    handout_type: HandoutType
    url: str | None
