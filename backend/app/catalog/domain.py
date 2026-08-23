"""Domain enums and invariants for the catalog domain."""

import enum
import uuid


class CreatureSize(enum.StrEnum):
    """Creature size categories from D&D 5e SRD."""

    small = "small"
    medium = "medium"


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
    """Item category types."""

    weapon = "weapon"
    armor = "armor"
    gear = "gear"
    consumable = "consumable"
    magic_item = "magic_item"


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


class CustomCampaignScopeError(ValueError):
    """Raised when a catalog entity violates the custom/campaign invariant."""


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
