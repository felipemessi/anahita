from .constants import BASE_AC, DEFAULT_DEX_BONUS_CAP
from .types import ArmorData


def calculate_ac(
    armor: ArmorData | None, dex_mod: int, shield_bonus: int = 0, misc_bonuses: int = 0
) -> int:
    """Calculate AC from armor, dex modifier, shields, and misc bonuses."""
    if not armor or armor.armor_type == "none":
        # Unarmored
        base_ac = BASE_AC + dex_mod
    else:
        base_ac = armor.base_ac
        if armor.armor_type == "light":
            base_ac += dex_mod
        elif armor.armor_type == "medium":
            base_ac += min(
                dex_mod,
                armor.dex_bonus_cap if armor.dex_bonus_cap is not None else DEFAULT_DEX_BONUS_CAP,
            )
        elif armor.armor_type == "heavy":
            # Heavy armor doesn't use dexterity modifier
            pass

    return base_ac + shield_bonus + misc_bonuses
