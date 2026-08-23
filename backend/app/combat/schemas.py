"""Pydantic request/response schemas for the combat domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.combat.domain import EncounterStatus


class EncounterCreate(BaseModel):
    """Request body to create an encounter within a session."""

    name: str = Field(min_length=1, max_length=255)


class EncounterParticipantCreate(BaseModel):
    """Request body to add a participant to an encounter.

    `character_id`/`npc_id` are mutually exclusive — see
    `app.combat.domain.validate_participant_kind`. Neither set means a
    manual/generic entry, identified only by `name`.
    """

    character_id: uuid.UUID | None = None
    npc_id: uuid.UUID | None = None
    name: str = Field(min_length=1, max_length=255)
    initiative: int
    hit_point_max: int = Field(ge=1)
    hit_point_current: int | None = Field(default=None, ge=0)
    armor_class: int = Field(ge=0)
    turn_order: int


class EncounterParticipantUpdate(BaseModel):
    """Request body to update a participant outside the live turn flow.

    Every field is optional — only the ones supplied are changed (mirrors
    `characters.schemas.CharacterUpdate`).
    """

    hit_point_current: int | None = Field(default=None, ge=0)
    temporary_hit_points: int | None = Field(default=None, ge=0)
    armor_class: int | None = Field(default=None, ge=0)
    initiative: int | None = None
    turn_order: int | None = None
    is_active: bool | None = None


class EncounterParticipantRead(BaseModel):
    """Response schema for an encounter participant."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    encounter_id: uuid.UUID
    character_id: uuid.UUID | None
    npc_id: uuid.UUID | None
    name: str
    initiative: int
    hit_point_max: int
    hit_point_current: int
    temporary_hit_points: int
    armor_class: int
    turn_order: int
    is_active: bool


class EncounterRead(BaseModel):
    """Response schema for an encounter, with its participants."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    name: str
    status: EncounterStatus
    current_round: int
    current_turn_order: int
    created_at: datetime
    participants: list[EncounterParticipantRead]
