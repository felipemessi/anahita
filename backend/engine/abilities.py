import math

from .constants import BASE_ABILITY_SCORE, TIER_1_PROFICIENCY_BONUS


def calculate_modifier(score: int) -> int:
    """Calculate ability modifier from an ability score."""
    return math.floor((score - BASE_ABILITY_SCORE) / 2)


def calculate_proficiency_bonus(total_level: int) -> int:
    """Calculate proficiency bonus based on character level."""
    if total_level < 1:
        return TIER_1_PROFICIENCY_BONUS  # Monsters and tier 1 fallback
    return math.ceil(total_level / 4) + 1


def calculate_skill_bonus(
    ability_mod: int, is_proficient: bool, has_expertise: bool, prof_bonus: int
) -> int:
    """Calculate the total bonus for a skill."""
    bonus = ability_mod
    if is_proficient:
        bonus += prof_bonus
        if has_expertise:
            bonus += prof_bonus
    return bonus


def calculate_saving_throw_bonus(
    ability_mod: int, is_proficient: bool, prof_bonus: int
) -> int:
    """Calculate the total bonus for a saving throw."""
    return ability_mod + prof_bonus if is_proficient else ability_mod
