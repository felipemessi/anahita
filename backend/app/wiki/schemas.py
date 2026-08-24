"""Pydantic request/response schemas for the wiki domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WikiPageCreate(BaseModel):
    """Request body to create a wiki page. `slug` is derived from `title`."""

    title: str = Field(min_length=1, max_length=255)
    content: str = ""
    tags: str | None = None


class WikiPageUpdate(BaseModel):
    """Request body to update a wiki page. Omitted fields are unchanged.

    Updating `title` regenerates `slug` from the new title.
    """

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = None
    tags: str | None = None


class WikiPageLinkCreate(BaseModel):
    """Request body to link a wiki page to an NPC, location, or faction.

    Exactly one of `npc_id`, `location_id`, `faction_id` must be set.
    """

    npc_id: uuid.UUID | None = None
    location_id: uuid.UUID | None = None
    faction_id: uuid.UUID | None = None


class WikiPageLinkRead(BaseModel):
    """Response schema for a wiki page link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    wiki_page_id: uuid.UUID
    npc_id: uuid.UUID | None
    location_id: uuid.UUID | None
    faction_id: uuid.UUID | None


class WikiPageSummary(BaseModel):
    """Summary response schema for a wiki page — used in list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    slug: str
    tags: str | None


class WikiPageRead(BaseModel):
    """Full response schema for a wiki page, including its links."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    title: str
    slug: str
    content: str
    tags: str | None
    created_by_id: uuid.UUID | None
    created_at: datetime
    links: list[WikiPageLinkRead] = []
