"""Characters domain enums and invariants."""

import enum
import uuid

# Re-exported for convenience: CharacterAbilityScore.ability uses the same six
# values as the catalog's AbilityScore, so character sheets and catalog data
# (e.g. Race.ability bonuses) speak the same vocabulary.
from app.catalog.domain import AbilityScore as AbilityScore  # noqa: F401


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
