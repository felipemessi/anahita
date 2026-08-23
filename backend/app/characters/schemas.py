"""Pydantic request/response schemas for the characters domain."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.domain import AbilityScore
from app.characters.domain import Skill


class CharacterAbilityScoreCreate(BaseModel):
    """One ability score supplied when creating a character."""

    ability: AbilityScore
    base_score: int = Field(ge=1, le=30)
    asi_bonus: int = 0
    misc_bonus: int = 0


class CharacterAbilityScoreRead(BaseModel):
    """Response schema for a character's ability score.

    `modifier` is computed by `engine.abilities.calculate_modifier` — it is
    never persisted, only derived on read.
    """

    id: uuid.UUID
    ability: AbilityScore
    base_score: int
    asi_bonus: int
    misc_bonus: int
    modifier: int


class CharacterSkillRead(BaseModel):
    """Response schema for a character's skill.

    `ability` (the governing ability) and `bonus` (via
    `engine.abilities.calculate_skill_bonus`) are computed, never persisted.
    """

    id: uuid.UUID
    skill: Skill
    ability: AbilityScore
    proficient: bool
    expertise: bool
    bonus: int


class CharacterClassCreate(BaseModel):
    """One class level entry supplied when creating a character."""

    class_definition_id: uuid.UUID
    subclass_id: uuid.UUID | None = None
    level: int = Field(default=1, ge=1, le=20)


class CharacterClassRead(BaseModel):
    """Response schema for a character's class entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    class_definition_id: uuid.UUID
    subclass_id: uuid.UUID | None
    level: int


class CharacterCreate(BaseModel):
    """Request body to create a character."""

    campaign_member_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    race_id: uuid.UUID
    subrace_id: uuid.UUID | None = None
    level: int = Field(default=1, ge=1, le=20)
    experience_points: int = 0
    alignment: str | None = None
    background: str | None = None
    temporary_hit_points: int = 0
    inspiration: bool = False
    ability_scores: list[CharacterAbilityScoreCreate]
    classes: list[CharacterClassCreate] = Field(min_length=1)


class CharacterUpdate(BaseModel):
    """Request body to update a character's combat-facing fields.

    Every field is optional — only the ones supplied are changed. Used by
    the inline HP editor on the character sheet (and future inline
    editors for AC/temp HP/inspiration).
    """

    hit_point_current: int | None = Field(default=None, ge=0)
    temporary_hit_points: int | None = Field(default=None, ge=0)
    armor_class: int | None = Field(default=None, ge=0)
    inspiration: bool | None = None


class CharacterRead(BaseModel):
    """Response schema for a character."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_member_id: uuid.UUID
    name: str
    race_id: uuid.UUID
    subrace_id: uuid.UUID | None
    level: int
    experience_points: int
    alignment: str | None
    background: str | None
    hit_point_max: int
    hit_point_current: int
    temporary_hit_points: int
    armor_class: int
    speed: int
    inspiration: bool
    proficiency_bonus: int
    ability_scores: list[CharacterAbilityScoreRead]
    skills: list[CharacterSkillRead]
    classes: list[CharacterClassRead]
