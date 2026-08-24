"""Pydantic request/response schemas for the journal domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class JournalEntryCreate(BaseModel):
    """Request body to create a journal entry."""

    title: str = Field(min_length=1, max_length=255)
    content: str = ""
    session_id: uuid.UUID | None = None


class JournalEntryUpdate(BaseModel):
    """Request body to update a journal entry. Omitted fields are unchanged."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    session_id: uuid.UUID | None = None


class JournalEntryRead(BaseModel):
    """Response schema for a journal entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    author_id: uuid.UUID
    title: str
    content: str
    session_id: uuid.UUID | None
    created_at: datetime
