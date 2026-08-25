"""Dice expression parsing and rolling (PRD §10.2, backlog Fase 6 história 6).

Every roll the backend makes on a player's behalf — initiative, attack,
damage — goes through this module by default; the caller may instead accept
a client-supplied `manual_result` and skip rolling entirely (see
`app.combat.service`). Expressions look like `"1d20+5"` or `"2d6"`, plus the
SRD's rare `"1d8 + MOD"` form (e.g. Spiritual Weapon) — `MOD` is substituted
with a caller-supplied ability modifier before parsing, never evaluated as
dice itself.
"""

import random
import re
from dataclasses import dataclass, field

_TERM_RE = re.compile(r"([+-]?)(\d*D\d+|\d+)")


@dataclass(frozen=True)
class DiceRoll:
    """The result of rolling a dice expression: total plus each individual die."""

    expression: str
    total: int
    rolls: list[int] = field(default_factory=list)


def roll(
    expression: str, *, modifier: int = 0, rng: random.Random | None = None
) -> DiceRoll:
    """Roll a dice expression like `"1d20+5"`, `"2d6"`, or `"1d8 + MOD"`.

    `modifier` substitutes the literal `MOD` token some SRD spell damage
    strings carry, spliced in as a signed integer before parsing. `rng` is
    injectable for deterministic tests — defaults to a fresh
    `random.Random()` instance (not the `random` module's shared global
    state, so concurrent rolls/tests never interfere with each other).
    """
    normalized = re.sub(r"\s+", "", expression.upper()).replace("MOD", str(modifier))
    # Cleanup for when substituting a negative modifier collides with a
    # literal "+"/"-" already in the expression (e.g. "1D8+-2" -> "1D8-2").
    normalized = (
        normalized.replace("+-", "-").replace("-+", "-").replace("++", "+")
    )

    roller = rng if rng is not None else random.Random()
    rolls: list[int] = []
    total = 0
    matched_any = False
    for match in _TERM_RE.finditer(normalized):
        matched_any = True
        sign = -1 if match.group(1) == "-" else 1
        term = match.group(2)
        if "D" in term:
            count_str, sides_str = term.split("D")
            count = int(count_str) if count_str else 1
            sides = int(sides_str)
            term_rolls = [roller.randint(1, sides) for _ in range(count)]
            rolls.extend(term_rolls)
            total += sign * sum(term_rolls)
        else:
            total += sign * int(term)

    if not matched_any:
        raise ValueError(f"Invalid dice expression: {expression!r}")
    return DiceRoll(expression=expression, total=total, rolls=rolls)


def roll_d20(*, bonus: int = 0, rng: random.Random | None = None) -> DiceRoll:
    """Roll `1d20 + bonus` — the common case for attack rolls and initiative."""
    sign = "+" if bonus >= 0 else ""
    return roll(f"1d20{sign}{bonus}", rng=rng)
