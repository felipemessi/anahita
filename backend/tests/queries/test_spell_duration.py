"""Tests for the cross-domain concentration-remaining-duration query."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
from app.characters.models import Character
from app.combat.domain import EncounterStatus
from app.combat.models import Encounter
from app.queries.spell_duration import get_concentration_remaining


async def _make_character(db: AsyncSession, **overrides: object) -> Character:
    character = Character(
        campaign_member_id=uuid.uuid4(),
        name="Aldric",
        race_id=uuid.uuid4(),
        level=1,
        hit_point_max=10,
        hit_point_current=10,
        armor_class=14,
        speed=30,
        proficiency_bonus=2,
        **overrides,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)
    return character


async def test_not_concentrating_returns_none_mode(db: AsyncSession) -> None:
    """A character concentrating on nothing has no remaining duration to report."""
    character = await _make_character(db)
    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode is None
    assert remaining.expired is False


async def test_indefinite_duration_has_no_clock(db: AsyncSession) -> None:
    """A concentration spell with nothing to track (e.g. "Until dispelled") is indefinite."""
    character = await _make_character(db, concentrating_spell_id=uuid.uuid4())
    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "indefinite"
    assert remaining.expired is False


async def test_rounds_mode_computes_remaining_from_encounter_round(
    db: AsyncSession,
) -> None:
    """Cast at round 3 with a 10-round duration, encounter now at round 5: 8 left."""
    encounter = Encounter(
        session_id=uuid.uuid4(),
        name="Ambush",
        status=EncounterStatus.active,
        current_round=5,
    )
    db.add(encounter)
    await db.flush()
    character = await _make_character(
        db,
        concentrating_spell_id=uuid.uuid4(),
        concentration_encounter_id=encounter.id,
        concentration_round_started=3,
        concentration_duration_rounds=10,
    )

    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "rounds"
    assert remaining.remaining_rounds == 8
    assert remaining.expired is False


async def test_rounds_mode_expires_once_elapsed_rounds_reach_duration(
    db: AsyncSession,
) -> None:
    """Once as many rounds have passed as the duration allows, it's expired (clamped at 0)."""
    encounter = Encounter(
        session_id=uuid.uuid4(),
        name="Ambush",
        status=EncounterStatus.active,
        current_round=20,
    )
    db.add(encounter)
    await db.flush()
    character = await _make_character(
        db,
        concentrating_spell_id=uuid.uuid4(),
        concentration_encounter_id=encounter.id,
        concentration_round_started=3,
        concentration_duration_rounds=10,
    )

    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "rounds"
    assert remaining.remaining_rounds == 0
    assert remaining.expired is True


async def test_seconds_mode_computes_remaining_from_now(db: AsyncSession) -> None:
    """Out-of-combat concentration counts down real time to `concentration_expires_at`."""
    character = await _make_character(
        db,
        concentrating_spell_id=uuid.uuid4(),
        concentration_expires_at=datetime.now(UTC) + timedelta(seconds=90),
    )

    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "seconds"
    assert remaining.remaining_seconds is not None
    assert 0 < remaining.remaining_seconds <= 90
    assert remaining.expired is False


async def test_seconds_mode_expired_once_the_deadline_has_passed(
    db: AsyncSession,
) -> None:
    """A `concentration_expires_at` in the past reports 0 remaining seconds, expired."""
    character = await _make_character(
        db,
        concentrating_spell_id=uuid.uuid4(),
        concentration_expires_at=datetime.now(UTC) - timedelta(seconds=5),
    )

    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "seconds"
    assert remaining.remaining_seconds == 0.0
    assert remaining.expired is True


async def test_rounds_mode_falls_back_to_indefinite_when_encounter_is_gone(
    db: AsyncSession,
) -> None:
    """A deleted/missing encounter can't be read for its current round — report indefinite."""
    character = await _make_character(
        db,
        concentrating_spell_id=uuid.uuid4(),
        concentration_encounter_id=uuid.uuid4(),
        concentration_round_started=1,
        concentration_duration_rounds=10,
    )

    remaining = await get_concentration_remaining(character, db)
    assert remaining.mode == "indefinite"
