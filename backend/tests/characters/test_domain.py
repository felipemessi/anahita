"""Unit tests for characters domain helpers."""

import pytest

from app.catalog.domain import AbilityScore
from app.characters.domain import (
    STANDARD_ARRAY,
    AbilityGenerationMethod,
    InvalidAbilityGenerationError,
    parse_saving_throw_proficiencies,
    validate_ability_generation,
)


def test_parse_saving_throw_proficiencies_two_abilities() -> None:
    """Comma-separated full names map to the short `AbilityScore` codes."""
    result = parse_saving_throw_proficiencies("Strength, Constitution")
    assert result == {AbilityScore.str, AbilityScore.con}


def test_parse_saving_throw_proficiencies_ignores_unknown_text() -> None:
    """Unrecognized entries are dropped instead of raising."""
    result = parse_saving_throw_proficiencies("Wisdom, Charisma, Nonsense")
    assert result == {AbilityScore.wis, AbilityScore.cha}


def test_parse_saving_throw_proficiencies_empty_string() -> None:
    """An empty string yields no proficiencies."""
    assert parse_saving_throw_proficiencies("") == set()


def test_point_buy_within_budget_passes() -> None:
    """A point buy spend within the 27-point budget raises nothing."""
    validate_ability_generation(
        AbilityGenerationMethod.point_buy, [15, 15, 8, 8, 8, 8]
    )


def test_point_buy_over_budget_rejected() -> None:
    """Spending more than 27 points on point buy is rejected."""
    with pytest.raises(InvalidAbilityGenerationError):
        validate_ability_generation(
            AbilityGenerationMethod.point_buy, [15, 15, 15, 15, 15, 15]
        )


def test_point_buy_score_out_of_range_rejected() -> None:
    """A base score outside 8-15 is never valid for point buy."""
    with pytest.raises(InvalidAbilityGenerationError):
        validate_ability_generation(
            AbilityGenerationMethod.point_buy, [16, 8, 8, 8, 8, 8]
        )


def test_standard_array_correct_permutation_passes() -> None:
    """The standard array values, in any order, are accepted."""
    validate_ability_generation(
        AbilityGenerationMethod.standard_array, list(reversed(STANDARD_ARRAY))
    )


def test_standard_array_wrong_values_rejected() -> None:
    """Any value outside the fixed standard array set is rejected."""
    with pytest.raises(InvalidAbilityGenerationError):
        validate_ability_generation(
            AbilityGenerationMethod.standard_array, [15, 14, 13, 12, 10, 9]
        )


def test_custom_and_roll_accept_any_values() -> None:
    """`custom`/`roll` never validate the actual numbers."""
    validate_ability_generation(AbilityGenerationMethod.custom, [3, 3, 3, 3, 3, 3])
    validate_ability_generation(AbilityGenerationMethod.roll, [18, 18, 18, 18, 18, 18])
