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


class AbilityGenerationMethod(enum.StrEnum):
    """How a player generated a character's base ability scores (PHB)."""

    standard_array = "standard_array"
    point_buy = "point_buy"
    custom = "custom"
    roll = "roll"


class InvalidAbilityGenerationError(ValueError):
    """Raised when base ability scores don't satisfy the declared generation method."""


#: PHB point-buy cost table (base score -> point cost), scores 8-15 only.
POINT_BUY_COSTS: dict[int, int] = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27

#: The fixed standard array values (PHB) — each used exactly once.
STANDARD_ARRAY: tuple[int, ...] = (15, 14, 13, 12, 10, 8)


def validate_ability_generation(
    method: AbilityGenerationMethod, base_scores: list[int]
) -> None:
    """Enforce the declared generation method's rules on base ability scores.

    `point_buy` scores must each be within 8-15 and spend no more than the
    27-point budget (PHB point-buy table); `standard_array` must use each of
    `STANDARD_ARRAY` exactly once. `custom`/`roll` accept any values — the
    client decides the numbers for those methods.
    """
    if method is AbilityGenerationMethod.point_buy:
        if any(score not in POINT_BUY_COSTS for score in base_scores):
            raise InvalidAbilityGenerationError(
                "Point buy base scores must be between 8 and 15."
            )
        total_cost = sum(POINT_BUY_COSTS[score] for score in base_scores)
        if total_cost > POINT_BUY_BUDGET:
            raise InvalidAbilityGenerationError(
                f"Point buy spent {total_cost} points, over the "
                f"{POINT_BUY_BUDGET}-point budget."
            )
    elif method is AbilityGenerationMethod.standard_array:
        if sorted(base_scores) != sorted(STANDARD_ARRAY):
            raise InvalidAbilityGenerationError(
                f"Standard array must use each of {STANDARD_ARRAY} exactly once."
            )


#: Maps the SRD's full ability names (as used in
#: `ClassDefinition.saving_throw_proficiencies`, e.g. "Strength, Constitution")
#: to our short `AbilityScore` codes.
ABILITY_FULL_NAME_TO_CODE: dict[str, AbilityScore] = {
    "Strength": AbilityScore.str,
    "Dexterity": AbilityScore.dex,
    "Constitution": AbilityScore.con,
    "Intelligence": AbilityScore.int,
    "Wisdom": AbilityScore.wis,
    "Charisma": AbilityScore.cha,
}


def parse_saving_throw_proficiencies(text: str) -> set[AbilityScore]:
    """Parse a `ClassDefinition.saving_throw_proficiencies` string (PHB rules).

    Only a character's starting class grants saving throw proficiencies —
    multiclassing never adds more (PHB multiclassing rules) — so callers
    should only parse the primary class's string.
    """
    return {
        ABILITY_FULL_NAME_TO_CODE[name.strip()]
        for name in text.split(",")
        if name.strip() in ABILITY_FULL_NAME_TO_CODE
    }


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


#: `Skill` uses underscores (`animal_handling`); `SkillDefinition.index` (and
#: `Proficiency.skill_id` -> `SkillDefinition`) uses hyphens
#: (`animal-handling`), the SRD's own convention — this bridges the two so
#: `CharacterService` can match a catalog skill Proficiency back to the
#: character-domain `Skill` it corresponds to (Fase 10).
SKILL_TO_CATALOG_INDEX: dict[Skill, str] = {
    skill: skill.value.replace("_", "-") for skill in Skill
}
CATALOG_INDEX_TO_SKILL: dict[str, Skill] = {
    index: skill for skill, index in SKILL_TO_CATALOG_INDEX.items()
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
