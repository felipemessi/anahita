"""Pydantic request/response schemas for the characters domain."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.domain import AbilityScore
from app.characters.domain import AbilityGenerationMethod, FeatureSourceType, Skill


class CharacterAbilityScoreCreate(BaseModel):
    """One ability score supplied when creating a character."""

    ability: AbilityScore
    base_score: int = Field(ge=1, le=30)
    asi_bonus: int = 0
    misc_bonus: int = 0


class CharacterAbilityScoreRead(BaseModel):
    """Response schema for a character's ability score.

    `modifier` is computed by `engine.abilities.calculate_modifier` — it is
    never persisted, only derived on read. `save_proficient` is set once at
    character creation from the starting class's SRD saving throw
    proficiencies (PHB multiclassing rules — never granted again by later
    classes); `save_bonus` is computed from it, never persisted.
    """

    id: uuid.UUID
    ability: AbilityScore
    base_score: int
    asi_bonus: int
    misc_bonus: int
    modifier: int
    save_proficient: bool
    save_bonus: int


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
    hit_dice_used: int


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
    generation_method: AbilityGenerationMethod | None = None


class CharacterSpellCreate(BaseModel):
    """Request body to add a known/prepared spell to a character."""

    spell_id: uuid.UUID
    prepared: bool = False
    source_class: str | None = None


class CharacterSpellRead(BaseModel):
    """Response schema for a character's known spell.

    `level` (spell circle, 0 = cantrip) and `ritual` are resolved from the
    catalog `Spell` on read, never persisted on `CharacterSpell` — see
    `CharacterService._to_read`.
    """

    id: uuid.UUID
    spell_id: uuid.UUID
    prepared: bool
    source_class: str | None
    level: int
    ritual: bool


class CharacterSpellUpdate(BaseModel):
    """Request body to toggle a known spell's `prepared` flag."""

    prepared: bool


class CharacterSpellSlotRead(BaseModel):
    """Response schema for a character's spell slots at one level.

    `max` is derived from the catalog on read (see
    `CharacterService._max_spell_slots`), never persisted.
    """

    spell_level: int
    used: int
    max: int


class CharacterSpellCastRequest(BaseModel):
    """Request body to cast a known spell, consuming a spell slot.

    `cast_at_level` defaults to the spell's own level (no upcast).
    `as_ritual=True` casts without consuming a slot — only accepted when the
    spell has the ritual tag. `target_participant_id` is accepted and
    echoed back for the UI's benefit (which encounter participant the
    spell was aimed at) — this endpoint has no encounter context to
    validate it against, so it's never checked or persisted.
    """

    cast_at_level: int | None = Field(default=None, ge=1, le=9)
    as_ritual: bool = False
    target_participant_id: uuid.UUID | None = None


class CharacterHitDiceSpend(BaseModel):
    """One class's hit dice spent during a short rest to recover HP."""

    character_class_id: uuid.UUID
    count: int = Field(ge=1)
    # Pre-rolled total HP healed from these dice (already including the CON
    # modifier), same manual-override convention as combat's
    # `manual_damage_roll` — bypasses `engine/dice.py` entirely when set.
    manual_roll: int | None = Field(default=None, ge=0)


class CharacterRestRequest(BaseModel):
    """Request body to take a short or long rest.

    `hit_dice_spent` only applies to a short rest — one entry per class the
    player is spending dice from (multiclass characters may spend dice from
    more than one class in the same short rest). A long rest ignores it and
    instead restores dice automatically per the PHB rule (see
    `CharacterService.rest`).
    """

    rest_type: Literal["short", "long"]
    hit_dice_spent: list[CharacterHitDiceSpend] = Field(default_factory=list)


class CharacterFeatureChoiceInput(BaseModel):
    """One choice made for a level's choice feature (e.g. Fighting Style)."""

    feature_id: uuid.UUID
    feature_option_id: uuid.UUID


class CharacterLevelUpRequest(BaseModel):
    """Request body to level up a character by one level in one class.

    `class_definition_id` is a class the character already has (levels it
    up) or a new one (multiclasses into it at level 1) — same PHB
    prerequisite check as `add_class`. `ability_score_increases` and
    `feat_id` are mutually exclusive, and only accepted at a level that
    grants an ASI for that class (`ClassLevel.ability_score_bonuses`);
    `manual_hit_die_roll` overrides `engine/dice.py` rolling the class's
    hit die for the HP gained, same manual-override convention as
    `CharacterHitDiceSpend.manual_roll`. `feature_choices` picks a named
    option for every choice feature (e.g. Fighting Style, Pact Boon) granted
    at the new level — required whenever one is granted, see
    `CharacterService.level_up`.
    """

    class_definition_id: uuid.UUID
    subclass_id: uuid.UUID | None = None
    ability_score_increases: dict[AbilityScore, int] | None = None
    feat_id: uuid.UUID | None = None
    manual_hit_die_roll: int | None = Field(default=None, ge=1)
    feature_choices: list[CharacterFeatureChoiceInput] = []


class CharacterDeathSaveRequest(BaseModel):
    """Request body to roll a death saving throw at 0 hit points."""

    # Pre-rolled 1d20 result, same manual-override convention as
    # `CharacterHitDiceSpend.manual_roll` — bypasses `engine/dice.py`.
    manual_roll: int | None = Field(default=None, ge=1, le=20)


class CharacterConcentrationRequest(BaseModel):
    """Request body to start or end concentration on a known spell.

    `spell_id=None` ends concentration; a value starts it (replacing
    whatever the character was already concentrating on, PHB rule).
    """

    spell_id: uuid.UUID | None = None


class CharacterResourceRead(BaseModel):
    """Response schema for a trackable class resource (rage, ki, ...).

    `max` is derived from `ClassLevelResource` at the character's class
    level, same computed-field pattern as `CharacterSpellSlotRead.max`
    (Fase 7) — only resources in `CharacterService._RESOURCE_RECHARGE`
    (with `max > 0`) appear here.
    """

    resource_key: str
    used: int
    max: int
    last_feature_option_id: uuid.UUID | None = None


class CharacterEquipmentCreate(BaseModel):
    """Request body to add an item to a character's personal inventory."""

    item_id: uuid.UUID
    equipped: bool = False
    quantity: int = Field(default=1, ge=1)
    attunement: bool = False


class CharacterEquipmentRead(BaseModel):
    """Response schema for an item in a character's personal inventory."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    equipped: bool
    quantity: int
    attunement: bool


class CharacterEquipmentUpdate(BaseModel):
    """Request body to edit an inventory item. Every field is optional."""

    equipped: bool | None = None
    attunement: bool | None = None
    quantity: int | None = Field(default=None, ge=1)


class CharacterCurrencyRequest(BaseModel):
    """Request body to record a currency gain/spend, in copper pieces.

    `delta` is positive for a gain, negative for a spend — the resulting
    balance can never go below zero (422).
    """

    delta: int


class CharacterFeatureCreate(BaseModel):
    """Request body to record a class/feat feature on a character.

    Racial features live on `Race` itself (catalog), not here — see
    `app/characters/models.py::CharacterFeature`.
    """

    source_type: FeatureSourceType
    source_name: str = Field(min_length=1, max_length=255)
    feature_name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    level_acquired: int = Field(default=1, ge=1, le=20)


class CharacterFeatureRead(BaseModel):
    """Response schema for a character's recorded feature."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_type: FeatureSourceType
    source_name: str
    feature_name: str
    description: str | None
    level_acquired: int


class CharacterFeatureChoiceRead(BaseModel):
    """Response schema for a choice made for a level's choice feature."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    feature_id: uuid.UUID
    feature_option_id: uuid.UUID


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


class CharacterSummaryRead(BaseModel):
    """Response schema for another player's character on the campaign roster.

    Deliberately excludes ability scores, HP, spells, and equipment — a
    player should only see identity/build basics for characters they don't
    own (PRD §7.3 visibility lacuna); the owner and the campaign's DM get
    the full `CharacterRead` instead — see
    `CharacterService.list_characters_for_campaign`.
    """

    id: uuid.UUID
    campaign_member_id: uuid.UUID
    name: str
    race_id: uuid.UUID
    subrace_id: uuid.UUID | None
    level: int
    classes: list[CharacterClassRead]


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
    currency_cp: int
    generation_method: AbilityGenerationMethod | None
    death_save_successes: int
    death_save_failures: int
    is_dead: bool
    concentrating_spell_id: uuid.UUID | None
    # `10 + bonus` of the corresponding skill — same computed-field pattern
    # as `CharacterSkillRead.bonus` (Fase 7).
    passive_perception: int
    passive_investigation: int
    passive_insight: int
    resources: list[CharacterResourceRead]
    ability_scores: list[CharacterAbilityScoreRead]
    skills: list[CharacterSkillRead]
    classes: list[CharacterClassRead]
    spells: list[CharacterSpellRead]
    spell_slots: list[CharacterSpellSlotRead]
    equipment: list[CharacterEquipmentRead]
    features: list[CharacterFeatureRead]
    feature_choices: list[CharacterFeatureChoiceRead]


class CharacterSpellCastResponse(BaseModel):
    """Response for casting a spell: the updated character, plus cast context.

    `save_dc` is `8 + proficiency + spellcasting ability modifier`, the
    same DC the target's saving throw is rolled against — only populated
    when the spell's `action_type` is `saving_throw` (`None` otherwise,
    same convention as `EncounterParticipantRead.concentration_dc`, Fase 7).
    `target_participant_id` echoes the request field back unchanged.
    """

    character: CharacterRead
    save_dc: int | None = None
    target_participant_id: uuid.UUID | None = None


class CharacterDeathSaveResponse(BaseModel):
    """Response for rolling a death saving throw: character plus the roll.

    `roll_result` is the raw 1d20 (or `manual_roll` override) — the client
    doesn't need to re-derive it from the updated successes/failures to
    show the roll (Fase 8: dice-roll animation on the sheet).
    """

    character: CharacterRead
    roll_result: int


class CharacterHitDiceRollResult(BaseModel):
    """One class's hit dice roll from a short rest, in request order."""

    character_class_id: uuid.UUID
    roll_result: int
    modifier: int
    healed: int


class CharacterRestResponse(BaseModel):
    """Response for taking a rest: character plus any hit dice rolled.

    `hit_dice_rolls` is empty for a long rest (dice are restored, not
    rolled) and has one entry per `CharacterRestRequest.hit_dice_spent`
    item, in the same order, for a short rest (Fase 8: dice-roll animation
    on the sheet).
    """

    character: CharacterRead
    hit_dice_rolls: list[CharacterHitDiceRollResult] = Field(default_factory=list)
