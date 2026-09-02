"""Pydantic request/response schemas for the maps domain (backlog Fase 15)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SessionMapRead(BaseModel):
    """Response schema for a session's battle map."""

    id: uuid.UUID
    session_id: uuid.UUID
    name: str
    url: str
    width_px: int
    height_px: int
    grid_size_px: int
    created_at: datetime


class MapTokenCreate(BaseModel):
    """Request body to place a token on a map.

    `character_id`/`npc_id`/`monster_id` are mutually exclusive — see
    `app.maps.domain.validate_token_kind`. None set means a manual/generic
    token, identified only by `name`.
    """

    character_id: uuid.UUID | None = None
    npc_id: uuid.UUID | None = None
    monster_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    is_visible: bool = True


class MapTokenMove(BaseModel):
    """Request body to reposition a token — `PATCH /tokens/{id}`."""

    x: int = Field(ge=0)
    y: int = Field(ge=0)


class MapTokenRead(BaseModel):
    """Response schema for a map token."""

    id: uuid.UUID
    map_id: uuid.UUID
    character_id: uuid.UUID | None
    npc_id: uuid.UUID | None
    monster_id: uuid.UUID | None
    name: str
    x: int
    y: int
    is_visible: bool


class MapSnapshotRead(BaseModel):
    """The full live state of a map — sent as `state_sync` on WS connect."""

    map: SessionMapRead
    tokens: list[MapTokenRead]


class WSMoveTokenPayload(BaseModel):
    """Payload for the `move_token` WS command — mirrors `MapTokenMove`."""

    token_id: uuid.UUID
    x: int = Field(ge=0)
    y: int = Field(ge=0)
