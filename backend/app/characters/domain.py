"""Characters domain enums and invariants."""

import enum
import uuid

# Re-exported for convenience: CharacterAbilityScore.ability uses the same six
# values as the catalog's AbilityScore, so character sheets and catalog data
# (e.g. Race.ability bonuses) speak the same vocabulary.
from app.catalog.domain import AbilityScore as AbilityScore  # noqa: F401
from engine.types import Ability as EngineAbility


class Skill(enum.StrEnum):
    """The 18 D&D 5e skills, each governed by one ability score."""

    acrobatics = "acrobatics"
    animal_handling = "animal_handling"
    arcana = "arcana"
    athletics = "athletics"
    deception = "deception"
    history = "history"
    insight = "insight"
    intimidation = "intimidation"
    investigation = "investigation"
    medicine = "medicine"
    nature = "nature"
    perception = "perception"
    performance = "performance"
    persuasion = "persuasion"
    religion = "religion"
    sleight_of_hand = "sleight_of_hand"
    stealth = "stealth"
    survival = "survival"


class FeatureSourceType(enum.StrEnum):
    """Where a CharacterFeature originates from."""

    class_ = "class"
    feat = "feat"


#: The ability score that governs each skill check (PRD §7.3, standard 5e rules).
SKILL_ABILITY: dict[Skill, AbilityScore] = {
    Skill.acrobatics: AbilityScore.dex,
    Skill.animal_handling: AbilityScore.wis,
    Skill.arcana: AbilityScore.int,
    Skill.athletics: AbilityScore.str,
    Skill.deception: AbilityScore.cha,
    Skill.history: AbilityScore.int,
    Skill.insight: AbilityScore.wis,
    Skill.intimidation: AbilityScore.cha,
    Skill.investigation: AbilityScore.int,
    Skill.medicine: AbilityScore.wis,
    Skill.nature: AbilityScore.int,
    Skill.perception: AbilityScore.wis,
    Skill.performance: AbilityScore.cha,
    Skill.persuasion: AbilityScore.cha,
    Skill.religion: AbilityScore.int,
    Skill.sleight_of_hand: AbilityScore.dex,
    Skill.stealth: AbilityScore.dex,
    Skill.survival: AbilityScore.wis,
}


#: Ability score prerequisites to multiclass into (or out of) each SRD class
#: (PHB multiclassing rules, keyed by `ClassDefinition.index`).
#:
#: Fighter's real prerequisite is STR 13 *or* DEX 13 — `engine.validation.
#: validate_multiclass` only expresses AND-of-abilities, so this table
#: simplifies Fighter to STR 13. A DEX-based Fighter multiclassing check may
#: be rejected incorrectly; every other class's prerequisite here is exact.
MULTICLASS_ABILITY_REQUIREMENTS: dict[str, dict[EngineAbility, int]] = {
    "barbarian": {EngineAbility.STR: 13},
    "bard": {EngineAbility.CHA: 13},
    "cleric": {EngineAbility.WIS: 13},
    "druid": {EngineAbility.WIS: 13},
    "fighter": {EngineAbility.STR: 13},
    "monk": {EngineAbility.DEX: 13, EngineAbility.WIS: 13},
    "paladin": {EngineAbility.STR: 13, EngineAbility.CHA: 13},
    "ranger": {EngineAbility.DEX: 13, EngineAbility.WIS: 13},
    "rogue": {EngineAbility.DEX: 13},
    "sorcerer": {EngineAbility.CHA: 13},
    "warlock": {EngineAbility.CHA: 13},
    "wizard": {EngineAbility.INT: 13},
}


class CrossCampaignCatalogReferenceError(ValueError):
    """Raised when a character references custom catalog content it can't see."""


def validate_catalog_reference(
    *,
    is_custom: bool,
    entity_campaign_id: uuid.UUID | None,
    character_campaign_id: uuid.UUID,
) -> None:
    """Enforce that a Character only references catalog content it can see.

    A Character may reference SRD content (`is_custom=False`, global) or
    homebrew content custom to its own campaign (`is_custom=True`,
    `entity_campaign_id == character_campaign_id`). Referencing homebrew from
    a different campaign is never allowed — that would leak one table's
    content into another.
    """
    if is_custom and entity_campaign_id != character_campaign_id:
        raise CrossCampaignCatalogReferenceError(
            "Cannot reference custom catalog content from another campaign."
        )
