"""Unit tests for app.combat.domain: participant-kind rule and turn advancement."""

import uuid

import pytest

from app.combat.domain import (
    ParticipantKindError,
    TurnParticipant,
    advance_turn,
    validate_participant_kind,
)


def test_validate_participant_kind_rejects_both_set() -> None:
    """A participant cannot be both a character and an NPC."""
    with pytest.raises(ParticipantKindError):
        validate_participant_kind(character_id=uuid.uuid4(), npc_id=uuid.uuid4())


def test_validate_participant_kind_accepts_character_only() -> None:
    """A PC participant (character_id set, npc_id None) is valid."""
    validate_participant_kind(character_id=uuid.uuid4(), npc_id=None)


def test_validate_participant_kind_accepts_npc_only() -> None:
    """An NPC participant (npc_id set, character_id None) is valid."""
    validate_participant_kind(character_id=None, npc_id=uuid.uuid4())


def test_validate_participant_kind_accepts_neither() -> None:
    """A manual/generic participant (neither set) is valid."""
    validate_participant_kind(character_id=None, npc_id=None)


def _participant(turn_order: int, *, is_active: bool = True) -> TurnParticipant:
    return TurnParticipant(id=uuid.uuid4(), turn_order=turn_order, is_active=is_active)


def test_advance_turn_moves_to_next_participant_in_order() -> None:
    """Advancing from the first participant's turn moves to the second."""
    first, second, third = _participant(0), _participant(1), _participant(2)
    result = advance_turn(
        [first, second, third], current_round=1, current_turn_order=0
    )
    assert result.participant_id == second.id
    assert result.turn_order == 1
    assert result.round == 1


def test_advance_turn_wraps_and_increments_round() -> None:
    """Advancing past the last participant wraps to the first and bumps the round."""
    first, second = _participant(0), _participant(1)
    result = advance_turn([first, second], current_round=1, current_turn_order=1)
    assert result.participant_id == first.id
    assert result.turn_order == 0
    assert result.round == 2


def test_advance_turn_skips_inactive_participants() -> None:
    """A dead/fled participant never gets a turn."""
    first = _participant(0)
    dead = _participant(1, is_active=False)
    third = _participant(2)
    result = advance_turn([first, dead, third], current_round=1, current_turn_order=0)
    assert result.participant_id == third.id


def test_advance_turn_with_no_active_participants_is_a_no_op() -> None:
    """With nobody active, the round/turn stay put and no participant is returned."""
    result = advance_turn(
        [_participant(0, is_active=False)], current_round=3, current_turn_order=0
    )
    assert result == advance_turn([], current_round=3, current_turn_order=0)
    assert result.participant_id is None
    assert result.round == 3
    assert result.turn_order == 0


def test_advance_turn_recovers_when_current_turn_order_no_longer_active() -> None:
    """If the current participant just became inactive, resume from the first active one."""
    now_dead = _participant(0, is_active=False)
    next_up = _participant(1)
    result = advance_turn(
        [now_dead, next_up], current_round=1, current_turn_order=0
    )
    assert result.participant_id == next_up.id
