from engine.armor_class import calculate_ac
from engine.types import ArmorData


def test_calculate_ac_unarmored() -> None:
    """
    Ensure AC is 10 + DEX when not wearing any armor.
    """
    ac = calculate_ac(None, dex_mod=3)
    assert ac == 13


def test_calculate_ac_light_armor() -> None:
    """
    Ensure Light Armor adds full DEX modifier without caps.
    """
    armor = ArmorData(base_ac=11, armor_type="light")
    ac = calculate_ac(armor, dex_mod=4)  # 11 + 4 = 15
    assert ac == 15


def test_calculate_ac_medium_armor() -> None:
    """
    Ensure Medium Armor caps the DEX modifier added to the base AC.
    """
    armor = ArmorData(base_ac=14, armor_type="medium", dex_bonus_cap=2)

    # Dex mod 4, but capped at 2
    ac_high_dex = calculate_ac(armor, dex_mod=4)  # 14 + 2 = 16
    assert ac_high_dex == 16

    # Dex mod 1, below cap
    ac_low_dex = calculate_ac(armor, dex_mod=1)  # 14 + 1 = 15
    assert ac_low_dex == 15


def test_calculate_ac_heavy_armor() -> None:
    """
    Ensure Heavy Armor completely ignores any positive or negative DEX modifier.
    """
    armor = ArmorData(base_ac=18, armor_type="heavy")

    # Dex mod shouldn't matter
    ac_positive = calculate_ac(armor, dex_mod=4)
    assert ac_positive == 18

    ac_negative = calculate_ac(armor, dex_mod=-2)
    assert ac_negative == 18


def test_calculate_ac_with_shield_and_misc() -> None:
    """
    Ensure shield bonuses and miscellaneous (magical) bonuses stack appropriately.
    """
    armor = ArmorData(base_ac=18, armor_type="heavy")

    # Shield +2, Ring of Protection +1
    ac = calculate_ac(armor, dex_mod=0, shield_bonus=2, misc_bonuses=1)
    assert ac == 21
