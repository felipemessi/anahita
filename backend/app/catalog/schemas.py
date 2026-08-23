"""Pydantic read schemas for the catalog domain."""

import uuid

from pydantic import BaseModel, ConfigDict


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


class SpellRead(BaseModel):
    """Read schema for a spell."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    level: int
    school: str
    casting_time: str
    range: str
    duration: str
    components: str
    ritual: bool
    concentration: bool
    description: str
    higher_levels: str | None


class SpellSummary(BaseModel):
    """Lightweight spell listing schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    level: int
    school: str
    ritual: bool
    concentration: bool


class WeaponDetailRead(BaseModel):
    """Read schema for weapon combat details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    damage_dice: str
    damage_type: str
    weapon_range: str
    weapon_properties: str | None


class ArmorDetailRead(BaseModel):
    """Read schema for armor defense details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    base_ac: int
    dex_bonus_cap: int | None
    stealth_disadvantage: bool
    strength_requirement: int | None


class ItemRead(BaseModel):
    """Read schema for an item."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    item_type: str
    rarity: str | None
    weight: float
    cost: int
    description: str
    properties: str | None
    weapon_detail: WeaponDetailRead | None
    armor_detail: ArmorDetailRead | None


class ItemSummary(BaseModel):
    """Lightweight item listing schema."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    item_type: str
    rarity: str | None
    weight: float
    cost: int


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
