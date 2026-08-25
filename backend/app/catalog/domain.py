"""Domain enums and invariants for the catalog domain."""

import enum
import uuid


class CreatureSize(enum.StrEnum):
    """Creature size categories from D&D 5e SRD.

    `Race.size` only ever uses `small`/`medium` (PC races); `Monster.size`
    (PRD §7.4.8) uses the full range.
    """

    tiny = "tiny"
    small = "small"
    medium = "medium"
    large = "large"
    huge = "huge"
    gargantuan = "gargantuan"


class AbilityScore(enum.StrEnum):
    """The six core ability scores."""

    str = "str"
    dex = "dex"
    con = "con"
    int = "int"
    wis = "wis"
    cha = "cha"


class SpellSchool(enum.StrEnum):
    """Schools of magic from D&D 5e SRD."""

    abjuration = "abjuration"
    conjuration = "conjuration"
    divination = "divination"
    enchantment = "enchantment"
    evocation = "evocation"
    illusion = "illusion"
    necromancy = "necromancy"
    transmutation = "transmutation"


class ItemType(enum.StrEnum):
    """Item category types (mundane equipment — see PRD §7.4.6).

    Magic items are a separate catalog category (`MagicItem`, PRD §7.4.6),
    not an `Item.item_type` value.
    """

    weapon = "weapon"
    armor = "armor"
    gear = "gear"
    tool = "tool"
    consumable = "consumable"


class ItemRarity(enum.StrEnum):
    """Magic item rarity tiers."""

    common = "common"
    uncommon = "uncommon"
    rare = "rare"
    very_rare = "very_rare"
    legendary = "legendary"
    artifact = "artifact"


class DamageType(enum.StrEnum):
    """Damage types from D&D 5e SRD."""

    acid = "acid"
    bludgeoning = "bludgeoning"
    cold = "cold"
    fire = "fire"
    force = "force"
    lightning = "lightning"
    necrotic = "necrotic"
    piercing = "piercing"
    poison = "poison"
    psychic = "psychic"
    radiant = "radiant"
    slashing = "slashing"
    thunder = "thunder"


class LanguageType(enum.StrEnum):
    """Language categories from D&D 5e SRD."""

    standard = "standard"
    exotic = "exotic"


class FeaturePrerequisiteType(enum.StrEnum):
    """Category of a FeaturePrerequisite, determining which field is checked."""

    level = "level"
    feature = "feature"
    spell = "spell"


class SpellDamageScalingType(enum.StrEnum):
    """How a SpellDamage entry's dice scale — never both for the same Spell.

    `slot_level`: scales with the spell slot it's cast at (e.g. Fireball).
    `character_level`: scales with the caster's class level instead —
    cantrips (Fire Bolt) rather than upcast leveled spells.
    """

    slot_level = "slot_level"
    character_level = "character_level"


class DamageModifierType(enum.StrEnum):
    """How strongly a Monster is affected by a damage type (PRD §7.4.8)."""

    vulnerable = "vulnerable"
    resistant = "resistant"
    immune = "immune"


class ProficiencyType(enum.StrEnum):
    """Category of a Proficiency, determining which FK on it is populated."""

    skill = "skill"
    saving_throw = "saving_throw"
    weapon = "weapon"
    armor = "armor"
    tool = "tool"
    other = "other"


#: Proficiency types whose granting reference is an equipment category
#: (`Proficiency.equipment_category_id`).
_EQUIPMENT_PROFICIENCY_TYPES = frozenset(
    {ProficiencyType.weapon, ProficiencyType.armor, ProficiencyType.tool}
)


class CustomCampaignScopeError(ValueError):
    """Raised when a catalog entity violates the custom/campaign invariant."""


class ProficiencyReferenceScopeError(ValueError):
    """Raised when a Proficiency's type/reference-FK combination is invalid."""


def validate_custom_campaign_scope(
    *, is_custom: bool, campaign_id: uuid.UUID | None
) -> None:
    """Enforce ``is_custom is False <=> campaign_id is None`` for catalog entities.

    SRD content is global (``is_custom=False``, ``campaign_id=None``); homebrew
    content is always scoped to the campaign that created it
    (``is_custom=True``, ``campaign_id`` set). Any other combination is invalid
    and must never reach the database — reused by every catalog service that
    creates content, mirroring the CHECK constraint enforced at the DB level
    (see `app.catalog.mixins.CatalogEntityMixin`).
    """
    if is_custom and campaign_id is None:
        raise CustomCampaignScopeError(
            "Custom catalog content must be scoped to a campaign_id."
        )
    if not is_custom and campaign_id is not None:
        raise CustomCampaignScopeError(
            "Non-custom (SRD) catalog content must not have a campaign_id."
        )


def validate_proficiency_reference_scope(
    *,
    proficiency_type: ProficiencyType,
    skill_id: uuid.UUID | None,
    ability_score_id: uuid.UUID | None,
    equipment_category_id: uuid.UUID | None,
) -> None:
    """Enforce that exactly the FK matching `proficiency_type` is populated.

    `Proficiency` has three nullable, mutually exclusive reference FKs
    (`skill_id`, `ability_score_id`, `equipment_category_id`) instead of a
    generic polymorphic reference. Which one (if any) must be set depends on
    `proficiency_type`:

    - `skill` -> `skill_id` only
    - `saving_throw` -> `ability_score_id` only
    - `weapon` / `armor` / `tool` -> `equipment_category_id` only
    - `other` -> none of them
    """
    refs = {
        "skill_id": skill_id,
        "ability_score_id": ability_score_id,
        "equipment_category_id": equipment_category_id,
    }
    if proficiency_type is ProficiencyType.skill:
        expected = "skill_id"
    elif proficiency_type is ProficiencyType.saving_throw:
        expected = "ability_score_id"
    elif proficiency_type in _EQUIPMENT_PROFICIENCY_TYPES:
        expected = "equipment_category_id"
    else:
        expected = None

    for name, value in refs.items():
        should_be_set = name == expected
        if should_be_set and value is None:
            raise ProficiencyReferenceScopeError(
                f"proficiency_type={proficiency_type} requires {name} to be set."
            )
        if not should_be_set and value is not None:
            raise ProficiencyReferenceScopeError(
                f"proficiency_type={proficiency_type} must not set {name}."
            )
