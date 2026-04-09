def calculate_max_hp(base_hp: int, level: int, con_mod: int, misc_bonuses: int = 0) -> int:
    """Calculate maximum hit points."""
    return base_hp + (con_mod * level) + misc_bonuses
