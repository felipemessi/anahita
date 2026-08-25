"""Pydantic read schemas for the catalog domain."""

import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.catalog.domain import (
    ItemType,
    SpellActionType,
    SpellDamageScalingType,
    SpellTargetType,
)


class RaceTraitRead(BaseModel):
    """Read schema for a racial trait."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trait_name: str
    description: str
    mechanical_effect: str | None


class SubraceTraitRead(BaseModel):
    """Read schema for a subrace trait."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    trait_name: str
    description: str
    mechanical_effect: str | None


class RaceAbilityBonusRead(BaseModel):
    """Read schema for a race ability bonus."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ability: str
    bonus: int


class SubraceRead(BaseModel):
    """Read schema for a subrace, with translated `name`/`description` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    traits: list[SubraceTraitRead]
    ability_bonuses: list[RaceAbilityBonusRead]


class RaceRead(BaseModel):
    """Read schema for a race, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    age: str
    alignment_desc: str
    size_description: str
    language_desc: str
    speed: int
    size: str
    darkvision_range: int
    is_custom: bool
    traits: list[RaceTraitRead]
    subraces: list[SubraceRead]
    ability_bonuses: list[RaceAbilityBonusRead]


class RaceSummary(BaseModel):
    """Lightweight race listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    speed: int
    size: str
    darkvision_range: int
    is_custom: bool


class FeaturePrerequisiteRead(BaseModel):
    """Read schema for a feature prerequisite."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prerequisite_type: str
    level: int | None
    required_feature_id: uuid.UUID | None
    spell_id: uuid.UUID | None


class FeatureRead(BaseModel):
    """Read schema for a class/subclass feature, with translated text resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    level: int
    feature_name: str
    description: str
    mechanical_effect: str | None
    parent_feature_id: uuid.UUID | None
    prerequisites: list[FeaturePrerequisiteRead]


class ClassLevelSpellSlotRead(BaseModel):
    """Read schema for a spell slot count at a class level."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    spell_level: int
    slot_count: int


class ClassLevelResourceRead(BaseModel):
    """Read schema for a structured class resource at a class level."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    resource_key: str
    value: str


class ClassLevelRead(BaseModel):
    """Read schema for one row of a class's level-by-level progression."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    level: int
    proficiency_bonus: int | None
    ability_score_bonuses: int | None
    features: list[FeatureRead]
    spell_slots: list[ClassLevelSpellSlotRead]
    resources: list[ClassLevelResourceRead]


class SubclassRead(BaseModel):
    """Read schema for a subclass, with translated text resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    flavor: str
    is_custom: bool
    features: list[FeatureRead]


class ClassDefinitionRead(BaseModel):
    """Read schema for a class definition, with translated text resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    hit_die: int
    primary_ability: str
    saving_throw_proficiencies: str
    is_custom: bool
    levels: list[ClassLevelRead]
    subclasses: list[SubclassRead]


class ClassSummary(BaseModel):
    """Lightweight class listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    hit_die: int
    primary_ability: str
    is_custom: bool


class SpellClassRead(BaseModel):
    """Read schema for a class that can cast a spell, with translated `name`."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class SpellDamageRead(BaseModel):
    """Read schema for one of a spell's damage entries, `damage_type` resolved.

    `scaling_key` is a slot level (1-9) when `scaling_type=slot_level`, or a
    character-level threshold (1/5/11/17) when `scaling_type=character_level`
    — see `app.catalog.models.SpellDamage`.
    """

    id: uuid.UUID
    damage_type: str
    scaling_type: SpellDamageScalingType
    scaling_key: int
    dice_expression: str


class SpellRead(BaseModel):
    """Read schema for a spell, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    duration: str
    components: str
    ritual: bool
    concentration: bool
    action_type: SpellActionType | None
    target_type: SpellTargetType | None
    save_ability_score_id: uuid.UUID | None
    description: str
    higher_levels: str | None
    is_custom: bool
    classes: list[SpellClassRead]
    damages: list[SpellDamageRead]


class SpellSummary(BaseModel):
    """Lightweight spell listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    level: int
    school: str
    ritual: bool
    concentration: bool
    is_custom: bool


class WeaponDetailRead(BaseModel):
    """Read schema for weapon combat details, with `damage_type` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    damage_dice: str
    damage_type: str
    weapon_range: str


class ArmorDetailRead(BaseModel):
    """Read schema for armor defense details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    base_ac: int
    dex_bonus_cap: int | None
    stealth_disadvantage: bool
    strength_requirement: int | None


class ItemPropertyRead(BaseModel):
    """Read schema for a weapon property carried by an item, with `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


class ItemRead(BaseModel):
    """Read schema for an item, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    item_type: str
    equipment_category: str
    rarity: str | None
    weight: float
    cost: int
    description: str
    is_custom: bool
    properties: list[ItemPropertyRead]
    weapon_detail: WeaponDetailRead | None
    armor_detail: ArmorDetailRead | None


class ItemSummary(BaseModel):
    """Lightweight item listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    item_type: str
    rarity: str | None
    weight: float
    cost: int
    is_custom: bool


class MagicItemSummary(BaseModel):
    """Lightweight magic item listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    rarity: str
    is_variant: bool
    variant_of_id: uuid.UUID | None
    is_custom: bool


class MagicItemRead(BaseModel):
    """Read schema for a magic item, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    equipment_category: str
    rarity: str
    is_custom: bool
    is_variant: bool
    variant_of_id: uuid.UUID | None
    variants: list[MagicItemSummary]


# --- Fixed vocabulary (SRD 2014 §7.4.1) -------------------------------------
#
# These entities have no `name`/translated text on the base row — that lives
# in the matching `_i18n` table (see `app.catalog.mixins`). Read schemas here
# expose only the structural fields; translated text is resolved separately
# via `app.catalog.service.get_translated` and composed by the caller once an
# endpoint needs it (no router yet for this fixed vocabulary — seed-only).


class AbilityScoreDefinitionRead(BaseModel):
    """Read schema for an ability score definition."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


class SkillDefinitionRead(BaseModel):
    """Read schema for a skill definition."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    ability_score_id: uuid.UUID
    is_custom: bool


class AlignmentRead(BaseModel):
    """Read schema for an alignment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


class ConditionRead(BaseModel):
    """Read schema for a condition."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


class DamageTypeRead(BaseModel):
    """Read schema for a damage type."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


class MagicSchoolRead(BaseModel):
    """Read schema for a school of magic."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


class LanguageRead(BaseModel):
    """Read schema for a language."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    language_type: str
    is_custom: bool


class WeaponPropertyRead(BaseModel):
    """Read schema for a weapon property."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    is_custom: bool


# --- Proficiencies (SRD 2014 §7.4.3) -----------------------------------------


class ProficiencyRead(BaseModel):
    """Read schema for a proficiency."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    proficiency_type: str
    skill_id: uuid.UUID | None
    ability_score_id: uuid.UUID | None
    equipment_category_id: uuid.UUID | None
    is_custom: bool


# --- Backgrounds and Feats (SRD 2014 §7.4.7) --------------------------------


class BackgroundEquipmentRead(BaseModel):
    """Read schema for a starting equipment grant, with `item_name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    item_id: uuid.UUID
    item_name: str
    quantity: int


class BackgroundFeatureRead(BaseModel):
    """Read schema for a background's signature feature."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    feature_name: str
    description: str


class BackgroundRead(BaseModel):
    """Read schema for a background, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    personality_traits: str
    ideals: str
    bonds: str
    flaws: str
    is_custom: bool
    proficiencies: list[ProficiencyRead]
    equipment: list[BackgroundEquipmentRead]
    feature: BackgroundFeatureRead | None


class BackgroundSummary(BaseModel):
    """Lightweight background listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    is_custom: bool


class FeatPrerequisiteRead(BaseModel):
    """Read schema for a feat's ability score prerequisite."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ability_score_id: uuid.UUID | None
    minimum_score: int


class FeatRead(BaseModel):
    """Read schema for a feat, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    is_custom: bool
    prerequisites: list[FeatPrerequisiteRead]


class FeatSummary(BaseModel):
    """Lightweight feat listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    is_custom: bool


# --- Monsters / stat blocks (SRD 2014 §7.4.8) -------------------------------


class MonsterSpeedRead(BaseModel):
    """Read schema for a monster's movement speeds."""

    model_config = ConfigDict(from_attributes=True)

    walk: str | None
    burrow: str | None
    climb: str | None
    fly: str | None
    swim: str | None
    hover: bool


class MonsterSenseRead(BaseModel):
    """Read schema for a monster's senses."""

    model_config = ConfigDict(from_attributes=True)

    passive_perception: int
    blindsight: str | None
    darkvision: str | None
    tremorsense: str | None
    truesight: str | None


class MonsterArmorClassRead(BaseModel):
    """Read schema for one AC entry of a monster."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    ac_type: str
    value: int
    condition_id: uuid.UUID | None
    description: str | None


class MonsterProficiencyRead(BaseModel):
    """Read schema for a monster's proficiency bonus on a skill/save."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    proficiency_id: uuid.UUID
    value: int


class MonsterDamageModifierRead(BaseModel):
    """Read schema for a monster's vulnerability/resistance/immunity.

    `damage_type` is resolved to its index (e.g. `fire`).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    damage_type: str
    modifier_type: str


class MonsterConditionImmunityRead(BaseModel):
    """Read schema for a monster's condition immunity, with `condition` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    condition: str


class MonsterActionDamageRead(BaseModel):
    """Read schema for a monster action's damage roll (`damage_type` resolved)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    damage_dice: str
    damage_type: str


class MonsterActionRead(BaseModel):
    """Shared read schema: action, legendary action, reaction, special ability."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str
    attack_bonus: int | None
    save_ability_score_id: uuid.UUID | None
    save_dc: int | None
    usage_type: str | None
    usage_times: int | None
    damages: list[MonsterActionDamageRead]


class MonsterRead(BaseModel):
    """Read schema for a monster stat block, with translated text fields resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    description: str
    size: str
    creature_type: str
    creature_subtype: str | None
    alignment: str
    hit_points: int
    hit_dice: str
    challenge_rating: float
    xp: int
    proficiency_bonus: int | None
    languages: str
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int
    is_custom: bool
    speed: MonsterSpeedRead | None
    senses: MonsterSenseRead | None
    armor_classes: list[MonsterArmorClassRead]
    proficiencies: list[MonsterProficiencyRead]
    damage_modifiers: list[MonsterDamageModifierRead]
    condition_immunities: list[MonsterConditionImmunityRead]
    actions: list[MonsterActionRead]
    legendary_actions: list[MonsterActionRead]
    reactions: list[MonsterActionRead]
    special_abilities: list[MonsterActionRead]


class MonsterSummary(BaseModel):
    """Lightweight monster listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    size: str
    creature_type: str
    challenge_rating: float
    is_custom: bool


# --- Rules narrativas (SRD 2014 §7.4.9) --------------------------------------


class RuleSectionRead(BaseModel):
    """Read schema for a rule section, with translated text resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    desc: str
    is_custom: bool


class RuleRead(BaseModel):
    """Read schema for a rule, with translated text and its sections resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    desc: str
    is_custom: bool
    sections: list[RuleSectionRead]


class RuleSummary(BaseModel):
    """Lightweight rule listing schema, with translated `name` resolved."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    index: str | None
    name: str
    is_custom: bool


# --- Homebrew creation (v1: races, classes, spells, items, monsters) ---------
#
# Every create schema is always scoped to a campaign — homebrew is never
# global (PRD §7.4, `app.catalog.domain.validate_custom_campaign_scope`).
# `campaign_id` and `is_custom=True` are never accepted from the client on
# these routes beyond `campaign_id` itself; the service always forces
# `is_custom=True`.


class RaceCreate(BaseModel):
    """Request body to create a homebrew race, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    description: str = ""
    speed: int = Field(default=30, ge=0)
    size: str = "medium"
    darkvision_range: int = Field(default=0, ge=0)


class ClassDefinitionCreate(BaseModel):
    """Request body to create a homebrew class, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    hit_die: int = Field(ge=4, le=12)
    primary_ability: str = Field(min_length=1, max_length=100)
    saving_throw_proficiencies: str = ""


class SpellCreate(BaseModel):
    """Request body to create a homebrew spell, always scoped to a campaign.

    `school` must match an existing `MagicSchool.index` (e.g. `evocation`) —
    the fixed SRD vocabulary (PRD §7.4.1), not free text.
    """

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    level: int = Field(ge=0, le=9)
    school: str
    casting_time: str = ""
    range: str = ""
    duration: str = ""
    components: str = ""
    ritual: bool = False
    concentration: bool = False
    action_type: SpellActionType | None = None
    target_type: SpellTargetType | None = None
    save_ability_score_id: uuid.UUID | None = None
    description: str = ""
    higher_levels: str | None = None


class ItemCreate(BaseModel):
    """Request body to create a homebrew item, always scoped to a campaign.

    Equipment category is derived from `item_type` (v1 simplification) —
    homebrew items don't pick a fine-grained SRD equipment category yet.
    """

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    item_type: ItemType
    rarity: str | None = None
    weight: float = Field(default=0.0, ge=0)
    cost: int = Field(default=0, ge=0)
    description: str = ""


class MonsterCreate(BaseModel):
    """Request body to create a homebrew monster, always scoped to a campaign.

    Fields beyond the v1 custom-entry form get sensible defaults
    (`hit_dice="1d8"`, ability scores 10) — full stat-block authoring is a
    future iteration.
    """

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    size: str
    creature_type: str = Field(min_length=1, max_length=100)
    alignment: str = "unaligned"
    hit_points: int = Field(ge=1)
    hit_dice: str = "1d8"
    challenge_rating: float = Field(ge=0)
    xp: int = Field(default=0, ge=0)
    languages: str = ""
    strength: int = Field(default=10, ge=1, le=30)
    dexterity: int = Field(default=10, ge=1, le=30)
    constitution: int = Field(default=10, ge=1, le=30)
    intelligence: int = Field(default=10, ge=1, le=30)
    wisdom: int = Field(default=10, ge=1, le=30)
    charisma: int = Field(default=10, ge=1, le=30)


class MagicItemCreate(BaseModel):
    """Request body to create a homebrew magic item, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    rarity: str = "common"


class BackgroundCreate(BaseModel):
    """Request body to create a homebrew background, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    personality_traits: str = ""
    ideals: str = ""
    bonds: str = ""
    flaws: str = ""


class FeatCreate(BaseModel):
    """Request body to create a homebrew feat, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=100)
    description: str = ""


class RuleCreate(BaseModel):
    """Request body to create a homebrew rule, always scoped to a campaign."""

    campaign_id: uuid.UUID
    name: str = Field(min_length=1, max_length=200)
    desc: str = ""
