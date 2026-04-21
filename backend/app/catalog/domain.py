"""Domain enums for the catalog domain."""

import enum


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
