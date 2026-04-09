from engine.abilities import calculate_modifier, calculate_proficiency_bonus, calculate_skill_bonus

def test_calculate_modifier():
    assert calculate_modifier(10) == 0
    assert calculate_modifier(11) == 0
    assert calculate_modifier(12) == 1
    assert calculate_modifier(13) == 1
    assert calculate_modifier(8) == -1
    assert calculate_modifier(9) == -1
    assert calculate_modifier(20) == 5

def test_calculate_proficiency_bonus():
    assert calculate_proficiency_bonus(1) == 2
    assert calculate_proficiency_bonus(4) == 2
    assert calculate_proficiency_bonus(5) == 3
    assert calculate_proficiency_bonus(9) == 4
    assert calculate_proficiency_bonus(13) == 5
    assert calculate_proficiency_bonus(17) == 6
    assert calculate_proficiency_bonus(20) == 6

def test_calculate_skill_bonus():
    # Str=16 (mod +3), Level=5 (prof +3)
    mod = 3
    prof = 3
    
    # Not proficient
    assert calculate_skill_bonus(mod, False, False, prof) == 3
    # Proficient
    assert calculate_skill_bonus(mod, True, False, prof) == 6
    # Expertise
    assert calculate_skill_bonus(mod, True, True, prof) == 9
