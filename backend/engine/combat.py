def calculate_attack_bonus(ability_mod: int, is_proficient: bool, prof_bonus: int, misc_bonuses: int = 0) -> int:
    """Calculate attack roll bonus."""
    bonus = ability_mod + misc_bonuses
    if is_proficient:
        bonus += prof_bonus
    return bonus

def calculate_save_dc(ability_mod: int, prof_bonus: int, misc_bonuses: int = 0) -> int:
    """Calculate spell/ability save DC."""
    return 8 + ability_mod + prof_bonus + misc_bonuses
