"""Unit tests for characters domain helpers."""

from app.catalog.domain import AbilityScore
from app.characters.domain import parse_saving_throw_proficiencies


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
