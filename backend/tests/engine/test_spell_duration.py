"""Unit tests for `engine.spell_duration` (pure SRD duration text parsing)."""

import pytest

from engine.spell_duration import (
    ROUND_SECONDS,
    parse_spell_duration,
    seconds_to_rounds,
)


@pytest.mark.parametrize(
    ("duration", "expected_seconds", "expected_cap"),
    [
        ("1 round", ROUND_SECONDS, False),
        ("1 minute", 60, False),
        ("10 minutes", 600, False),
        ("1 hour", 3600, False),
        ("24 hours", 86400, False),
        ("7 days", 7 * 86400, False),
        ("Up to 1 round", ROUND_SECONDS, True),
        ("Up to 1 minute", 60, True),
        ("Up to 10 minutes", 600, True),
        ("Up to 1 hour", 3600, True),
        ("Up to 2 hours", 7200, True),
        ("Up to 8 hours", 28800, True),
        ("Up to 24 hours", 86400, True),
    ],
)
def test_parse_spell_duration_timed_text(
    duration: str, expected_seconds: int, expected_cap: bool
) -> None:
    """Timed SRD duration text (with or without the concentration "Up to" cap)."""
    parsed = parse_spell_duration(duration)
    assert parsed.seconds == expected_seconds
    assert parsed.is_concentration_cap is expected_cap


@pytest.mark.parametrize(
    "duration", ["Instantaneous", "Special", "Until dispelled"]
)
def test_parse_spell_duration_indefinite_text_has_no_seconds(duration: str) -> None:
    """Text with no fixed span to track parses to `seconds=None`."""
    parsed = parse_spell_duration(duration)
    assert parsed.seconds is None
    assert parsed.is_concentration_cap is False


def test_parse_spell_duration_unrecognized_text_is_treated_as_indefinite() -> None:
    """Free text that doesn't match the SRD pattern doesn't crash — no clock to track."""
    parsed = parse_spell_duration("Until the next dawn")
    assert parsed.seconds is None


@pytest.mark.parametrize(
    ("seconds", "expected_rounds"),
    [
        (ROUND_SECONDS, 1),
        (60, 10),
        (600, 100),
        (3600, 600),
        (1, 1),  # rounds up, never below a single round
        (7, 2),  # doesn't divide evenly — rounds up
    ],
)
def test_seconds_to_rounds_rounds_up(seconds: int, expected_rounds: int) -> None:
    """Real-time seconds convert to whole combat rounds, rounded up."""
    assert seconds_to_rounds(seconds) == expected_rounds
