"""Unit tests for engine.dice: expression parsing, rolling, MOD substitution."""

import random

import pytest

from engine.dice import roll, roll_d20


def test_roll_single_die_with_flat_bonus() -> None:
    """A deterministic RNG makes the total predictable and verifiable."""
    rng = random.Random(1)
    expected_die = rng.randint(1, 8)
    result = roll("1d8+3", rng=random.Random(1))
    assert result.rolls == [expected_die]
    assert result.total == expected_die + 3


def test_roll_multiple_dice_sums_all() -> None:
    """"2d6" rolls two dice and sums them, no flat modifier."""
    result = roll("2d6", rng=random.Random(42))
    assert len(result.rolls) == 2
    assert all(1 <= r <= 6 for r in result.rolls)
    assert result.total == sum(result.rolls)


def test_roll_negative_flat_modifier() -> None:
    """A negative flat modifier subtracts from the dice total."""
    rng = random.Random(7)
    die = rng.randint(1, 4)
    result = roll("1d4-2", rng=random.Random(7))
    assert result.total == die - 2


def test_roll_mod_placeholder_substituted() -> None:
    """The "MOD" token is replaced with the caller-supplied modifier."""
    rng = random.Random(3)
    die = rng.randint(1, 8)
    result = roll("1d8 + MOD", modifier=4, rng=random.Random(3))
    assert result.total == die + 4


def test_roll_mod_placeholder_negative_modifier() -> None:
    """A negative MOD substitution doesn't produce an unparseable "+-"."""
    rng = random.Random(5)
    die = rng.randint(1, 8)
    result = roll("1d8 + MOD", modifier=-2, rng=random.Random(5))
    assert result.total == die - 2


def test_roll_invalid_expression_rejected() -> None:
    """A string with no dice/flat terms raises ValueError."""
    with pytest.raises(ValueError, match="Invalid dice expression"):
        roll("banana")


def test_roll_is_deterministic_with_same_seed() -> None:
    """The same seeded RNG always produces the same result."""
    first = roll("1d20+5", rng=random.Random(99))
    second = roll("1d20+5", rng=random.Random(99))
    assert first == second


def test_roll_d20_positive_bonus() -> None:
    """roll_d20 adds a positive bonus correctly."""
    rng = random.Random(11)
    die = rng.randint(1, 20)
    result = roll_d20(bonus=5, rng=random.Random(11))
    assert result.total == die + 5


def test_roll_d20_negative_bonus() -> None:
    """roll_d20 subtracts a negative bonus correctly."""
    rng = random.Random(13)
    die = rng.randint(1, 20)
    result = roll_d20(bonus=-2, rng=random.Random(13))
    assert result.total == die - 2
