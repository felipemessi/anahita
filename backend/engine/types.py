from dataclasses import dataclass
from enum import StrEnum


class Ability(StrEnum):
    STR = "str"
    DEX = "dex"
    CON = "con"
    INT = "int"
    WIS = "wis"
    CHA = "cha"


class ConditionType(StrEnum):
    BLINDED = "blinded"
    CHARMED = "charmed"
    DEAFENED = "deafened"
    EXHAUSTION = "exhaustion"
    FRIGHTENED = "frightened"
    GRAPPLED = "grappled"
    INCAPACITATED = "incapacitated"
    INVISIBLE = "invisible"
    PARALYZED = "paralyzed"
    PETRIFIED = "petrified"
    POISONED = "poisoned"
    PRONE = "prone"
    RESTRAINED = "restrained"
    STUNNED = "stunned"
    UNCONSCIOUS = "unconscious"


@dataclass
class MechanicalEffect:
    effect_type: str
    value: int | str | None = None
    target: str | None = None


@dataclass
class Condition:
    condition_type: ConditionType
    level: int = 1


@dataclass
class ArmorData:
    base_ac: int
    armor_type: str
    dex_bonus_cap: int | None = None
    strength_requirement: int | None = None
    stealth_disadvantage: bool = False


@dataclass
class CharacterContext:
    level: int
    ability_scores: dict[Ability, int]
    armor: ArmorData | None = None
    shield_bonus: int = 0
    misc_ac_bonus: int = 0
