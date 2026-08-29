"""Pydantic request/response schemas for the world-building domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.world.domain import (
    FactionRelationshipType,
    LocationType,
    NPCLocationPresenceType,
)


class NPCCreate(BaseModel):
    """Request body to create an NPC."""

    name: str = Field(min_length=1, max_length=255)
    race: str = Field(min_length=1, max_length=100)
    occupation: str | None = None
    description: str = ""
    personality: str | None = None
    is_alive: bool = True
    stat_block_id: uuid.UUID | None = None


class NPCRead(BaseModel):
    """Response schema for an NPC."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    race: str
    occupation: str | None
    description: str
    personality: str | None
    is_alive: bool
    stat_block_id: uuid.UUID | None
    is_revealed: bool
    created_at: datetime


class LocationCreate(BaseModel):
    """Request body to create a location."""

    name: str = Field(min_length=1, max_length=255)
    location_type: LocationType
    description: str = ""
    parent_location_id: uuid.UUID | None = None


class LocationRead(BaseModel):
    """Response schema for a location."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    location_type: LocationType
    description: str
    parent_location_id: uuid.UUID | None
    created_at: datetime


class LocationParentUpdate(BaseModel):
    """Request body to reparent a location within the hierarchy."""

    parent_location_id: uuid.UUID | None = None


class LocationTreeNode(BaseModel):
    """A location and its descendants, nested by `parent_location_id`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    location_type: LocationType
    children: list[LocationTreeNode] = []


class FactionCreate(BaseModel):
    """Request body to create a faction."""

    name: str = Field(min_length=1, max_length=255)
    description: str = ""
    alignment: str | None = None
    influence_level: str | None = None


class FactionRead(BaseModel):
    """Response schema for a faction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    description: str
    alignment: str | None
    influence_level: str | None


class NPCFactionCreate(BaseModel):
    """Request body to link an NPC to a Faction."""

    faction_id: uuid.UUID
    role_in_faction: str | None = None


class NPCFactionRead(BaseModel):
    """Response schema for an NPC-Faction link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    npc_id: uuid.UUID
    faction_id: uuid.UUID
    role_in_faction: str | None


class NPCLocationCreate(BaseModel):
    """Request body to link an NPC to a Location."""

    location_id: uuid.UUID
    presence_type: NPCLocationPresenceType


class NPCLocationRead(BaseModel):
    """Response schema for an NPC-Location link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    npc_id: uuid.UUID
    location_id: uuid.UUID
    presence_type: NPCLocationPresenceType


class NPCSessionCreate(BaseModel):
    """Request body to link an NPC to a Session appearance."""

    session_id: uuid.UUID
    appearance_note: str | None = None


class NPCSessionRead(BaseModel):
    """Response schema for an NPC-Session link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    npc_id: uuid.UUID
    session_id: uuid.UUID
    appearance_note: str | None


class LocationSessionCreate(BaseModel):
    """Request body to link a Location to a Session visit."""

    session_id: uuid.UUID
    visit_note: str | None = None


class LocationSessionRead(BaseModel):
    """Response schema for a Location-Session link."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    location_id: uuid.UUID
    session_id: uuid.UUID
    visit_note: str | None


class FactionRelationshipCreate(BaseModel):
    """Request body to set a relationship between two Factions."""

    faction_b_id: uuid.UUID
    relationship_type: FactionRelationshipType


class FactionRelationshipRead(BaseModel):
    """Response schema for a Faction relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    faction_a_id: uuid.UUID
    faction_b_id: uuid.UUID
    relationship_type: FactionRelationshipType


class WorldSearchResult(BaseModel):
    """One cross-entity search hit — an NPC, Location, or Faction."""

    entity_type: str
    id: uuid.UUID
    name: str
    snippet: str
