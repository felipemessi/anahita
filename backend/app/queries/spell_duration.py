"""Cross-domain query: remaining time on a character's active concentration.

Reads `Character.concentration_*` (characters domain, Fase 12) together with
`Encounter.current_round` (combat domain) to compute how much duration is
left on the spell the character is concentrating on — in rounds when it was
cast inside an encounter, in seconds otherwise. Lives here rather than in
`app.characters.service` because it spans both domains (same rationale as
`app.queries.character_sessions` spanning characters/combat/sessions).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.characters.models import Character
from app.combat.models import Encounter


@dataclass(frozen=True, slots=True)
class ConcentrationRemaining:
    """How much duration is left on a character's active concentration.

    `mode` is `None` when the character isn't concentrating on anything,
    `"indefinite"` when the spell's duration has no clock to track (see
    `engine.spell_duration.parse_spell_duration`) or its encounter could no
    longer be found, `"rounds"` inside an encounter, `"seconds"` otherwise.
    `expired` is `True` once the remaining time has reached zero — the
    concentration state itself isn't auto-cleared by reading it, only
    reported as expired, so the DM/player can still resolve the drop-off
    explicitly (matches how `EncounterCondition` durations are read, not
    auto-removed either).
    """

    mode: Literal["rounds", "seconds", "indefinite"] | None
    remaining_rounds: int | None = None
    remaining_seconds: float | None = None
    expired: bool = False


async def get_concentration_remaining(
    character: Character, db: AsyncSession
) -> ConcentrationRemaining:
    """Compute the remaining concentration duration for `character`."""
    if character.concentrating_spell_id is None:
        return ConcentrationRemaining(mode=None)

    if character.concentration_encounter_id is not None:
        if (
            character.concentration_duration_rounds is None
            or character.concentration_round_started is None
        ):
            return ConcentrationRemaining(mode="indefinite")
        encounter = await db.get(Encounter, character.concentration_encounter_id)
        if encounter is None:
            return ConcentrationRemaining(mode="indefinite")
        elapsed_rounds = encounter.current_round - character.concentration_round_started
        remaining_rounds = max(
            0, character.concentration_duration_rounds - elapsed_rounds
        )
        return ConcentrationRemaining(
            mode="rounds",
            remaining_rounds=remaining_rounds,
            expired=remaining_rounds <= 0,
        )

    if character.concentration_expires_at is not None:
        # Compare naively: SQLite round-trips DateTime(timezone=True) as
        # naive UTC, so mixing it with an aware `datetime.now(UTC)` raises
        # TypeError — same pattern as `CampaignService.accept_invite`.
        now = datetime.now(UTC).replace(tzinfo=None)
        remaining_seconds = max(
            0.0,
            (
                character.concentration_expires_at.replace(tzinfo=None) - now
            ).total_seconds(),
        )
        return ConcentrationRemaining(
            mode="seconds",
            remaining_seconds=remaining_seconds,
            expired=remaining_seconds <= 0,
        )

    return ConcentrationRemaining(mode="indefinite")
