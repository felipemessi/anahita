from engine.armor_class import calculate_ac
from engine.types import ArmorData

def test_calculate_ac_unarmored():
    ac = calculate_ac(None, dex_mod=3)
    assert ac == 13

def test_calculate_ac_light_armor():
    armor = ArmorData(base_ac=11, armor_type="light")
    ac = calculate_ac(armor, dex_mod=4)    # 11 + 4 = 15
    assert ac == 15

def test_calculate_ac_medium_armor():
    armor = ArmorData(base_ac=14, armor_type="medium", dex_bonus_cap=2)
    # Dex mod 4, but capped at 2
    ac = calculate_ac(armor, dex_mod=4)    # 14 + 2 = 16
    assert ac == 16
    
    # Dex mod 1, below cap
    ac_low = calculate_ac(armor, dex_mod=1) # 14 + 1 = 15
    assert ac_low == 15

def test_calculate_ac_heavy_armor():
    armor = ArmorData(base_ac=18, armor_type="heavy")
    # Dex mod shouldn't matter
    ac = calculate_ac(armor, dex_mod=4)
    assert ac == 18
    ac_neg = calculate_ac(armor, dex_mod=-2)
    assert ac_neg == 18

def test_calculate_ac_with_shield_and_misc():
    armor = ArmorData(base_ac=18, armor_type="heavy")
    # Shield +2, Ring of Protection +1
    ac = calculate_ac(armor, dex_mod=0, shield_bonus=2, misc_bonuses=1)
    assert ac == 21
