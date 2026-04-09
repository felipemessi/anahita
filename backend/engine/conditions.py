from .types import Condition, ConditionType, MechanicalEffect


def get_condition_effects(conditions: list[Condition]) -> list[MechanicalEffect]:
    """Resolve active conditions into explicit mechanical effects."""
    effects: list[MechanicalEffect] = []

    for cond in conditions:
        if cond.condition_type == ConditionType.BLINDED:
            effects.append(MechanicalEffect("attack_disadvantage", target="all"))
            effects.append(MechanicalEffect("attacks_against_advantage", target="all"))
            effects.append(MechanicalEffect("auto_fail_save", target="sight_based"))

        elif cond.condition_type == ConditionType.CHARMED:
            effects.append(MechanicalEffect("cannot_attack", target="charmer"))
            effects.append(MechanicalEffect("charmer_advantage", target="ability_checks_social"))

        elif cond.condition_type == ConditionType.RESTRAINED:
            effects.append(MechanicalEffect("speed_set", value=0))
            effects.append(MechanicalEffect("attack_disadvantage", target="self"))
            effects.append(MechanicalEffect("attacks_against_advantage", target="self"))
            effects.append(MechanicalEffect("save_disadvantage", target="dex"))

        elif cond.condition_type == ConditionType.PRONE:
            effects.append(MechanicalEffect("attack_disadvantage", target="melee"))
            effects.append(MechanicalEffect("attacks_against_advantage", target="melee_5ft"))
            effects.append(MechanicalEffect("attacks_against_disadvantage", target="ranged"))

        elif cond.condition_type == ConditionType.EXHAUSTION:
            if cond.level >= 1:
                effects.append(MechanicalEffect("ability_check_disadvantage", target="all"))
            if cond.level >= 2:
                effects.append(MechanicalEffect("speed_halved", target="all"))
            if cond.level >= 3:
                effects.append(MechanicalEffect("attack_disadvantage", target="all"))
                effects.append(MechanicalEffect("save_disadvantage", target="all"))
            if cond.level >= 4:
                effects.append(MechanicalEffect("hp_max_halved", target="self"))
            if cond.level >= 5:
                effects.append(MechanicalEffect("speed_set", value=0))
            if cond.level >= 6:
                effects.append(MechanicalEffect("death", target="self"))

    return effects
