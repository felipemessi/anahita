"""Pure parsing of SRD spell duration text into engine time units.

`catalog_spells.duration` is free-text straight from the SRD data
(`"1 minute"`, `"Up to 10 minutes"`, `"Instantaneous"`, `"Until dispelled"`,
`"Special"`, ...) — see `app/catalog/seeds/data/spells.json`. This module
turns that text into a number of real-time seconds so callers can decide,
depending on whether the spell was cast inside an encounter, whether to
track the remaining duration in rounds (combat time) or in wall-clock time
(out of combat).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

#: Seconds per combat round (PHB rule, same assumption already used for
#: `EncounterCondition.duration_rounds` — see `CombatService.declare_action`,
#: e.g. "1 minute at 6s/round").
ROUND_SECONDS = 6

_UNIT_SECONDS: dict[str, int] = {
    "round": ROUND_SECONDS,
    "minute": 60,
    "hour": 3600,
    "day": 86400,
}

_TIMED_PATTERN = re.compile(r"^(\d+)\s+(round|minute|hour|day)s?$")


@dataclass(frozen=True, slots=True)
class ParsedSpellDuration:
    """Result of parsing a spell's `duration` text.

    `seconds` is `None` for a duration with no timed expiry to track:
    "Instantaneous" (the effect resolves immediately, nothing lingers),
    "Special" (rules-text-defined, not a fixed span), or "Until dispelled"
    (indefinite — ends only by an explicit action, never by a clock).
    `is_concentration_cap` flags the SRD's "Up to X" phrasing, used on every
    concentration spell's duration text.
    """

    seconds: int | None
    is_concentration_cap: bool


_INDEFINITE_TEXTS = {"instantaneous", "special", "until dispelled"}


def parse_spell_duration(duration: str) -> ParsedSpellDuration:
    """Parse SRD duration text (e.g. `"Up to 1 minute"`) into engine units."""
    text = duration.strip()
    is_cap = text.lower().startswith("up to ")
    if is_cap:
        text = text[len("up to ") :]
    lowered = text.lower()
    if lowered in _INDEFINITE_TEXTS:
        return ParsedSpellDuration(seconds=None, is_concentration_cap=is_cap)
    match = _TIMED_PATTERN.match(lowered)
    if match is None:
        # Unrecognized text (shouldn't happen against SRD data, but a
        # homebrew/custom spell's free text might not match) — treat as
        # indefinite rather than guessing.
        return ParsedSpellDuration(seconds=None, is_concentration_cap=is_cap)
    amount = int(match.group(1))
    unit = match.group(2)
    return ParsedSpellDuration(
        seconds=amount * _UNIT_SECONDS[unit], is_concentration_cap=is_cap
    )


def seconds_to_rounds(seconds: int) -> int:
    """Convert a real-time duration to whole combat rounds, rounded up.

    Rounding up (rather than down/truncating) means a duration that doesn't
    divide evenly into 6-second rounds (there are none in the SRD today,
    but a homebrew spell might) never grants less combat time than its
    real-time text promises.
    """
    return max(1, -(-seconds // ROUND_SECONDS))
