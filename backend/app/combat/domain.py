"""Combat domain enums, invariants, and pure turn-order logic (PRD §7.6)."""

import uuid
from dataclasses import dataclass
from enum import StrEnum


class EncounterStatus(StrEnum):
    """Lifecycle status of an Encounter."""

    preparing = "preparing"
    active = "active"
    completed = "completed"


class ConditionType(StrEnum):
    """The 15 D&D 5e conditions — mirrors `engine.types.ConditionType` values.

    Kept as a separate (app-level) enum rather than importing the engine one
    directly, since the engine module has no I/O/framework dependencies and
    this one backs a database column — `app.combat.service` converts between
    the two when resolving mechanical effects (PRD §7.6, backlog Fase 2
    história 3).
    """

    blinded = "blinded"
    charmed = "charmed"
    deafened = "deafened"
    exhaustion = "exhaustion"
    frightened = "frightened"
    grappled = "grappled"
    incapacitated = "incapacitated"
    invisible = "invisible"
    paralyzed = "paralyzed"
    petrified = "petrified"
    poisoned = "poisoned"
    prone = "prone"
    restrained = "restrained"
    stunned = "stunned"
    unconscious = "unconscious"


class ActionType(StrEnum):
    """Category of a logged combat action (`CombatLog.action_type`)."""

    attack = "attack"
    spell = "spell"
    move = "move"
    dash = "dash"
    dodge = "dodge"
    disengage = "disengage"
    help = "help"
    hide = "hide"
    ready = "ready"
    other = "other"


class ParticipantKindError(ValueError):
    """Raised when an EncounterParticipant is linked to both a PC and an NPC."""


def validate_participant_kind(
    *, character_id: uuid.UUID | None, npc_id: uuid.UUID | None
) -> None:
    """Enforce that a participant is a PC **or** an NPC, never both.

    Neither being set is valid — it's a manual/generic participant (e.g. an
    unnamed monster added on the fly), identified only by its `name` field
    (PRD §7.6: "name: fallback para monstros genéricos").
    """
    if character_id is not None and npc_id is not None:
        raise ParticipantKindError(
            "An encounter participant cannot be both a character and an NPC."
        )


@dataclass(frozen=True)
class TurnParticipant:
    """Minimal shape `advance_turn` needs — decoupled from the ORM model."""

    id: uuid.UUID
    turn_order: int
    is_active: bool


@dataclass(frozen=True)
class TurnAdvanceResult:
    """The new round/turn-order after advancing, and whose turn it now is."""

    round: int
    turn_order: int
    participant_id: uuid.UUID | None


def advance_turn(
    participants: list[TurnParticipant],
    *,
    current_round: int,
    current_turn_order: int,
) -> TurnAdvanceResult:
    """Compute the next active participant's turn, advancing the round on wrap.

    Only `is_active` participants (not dead/fled) take turns. Turn order
    cycles through them sorted by `turn_order`; wrapping back to the first
    participant increments `current_round`. Returns the current state
    unchanged (with `participant_id=None`) if there are no active
    participants.
    """
    active = sorted(
        (p for p in participants if p.is_active), key=lambda p: p.turn_order
    )
    if not active:
        return TurnAdvanceResult(
            round=current_round, turn_order=current_turn_order, participant_id=None
        )

    order_values = [p.turn_order for p in active]
    try:
        index = order_values.index(current_turn_order)
        next_index = (index + 1) % len(order_values)
    except ValueError:
        # current_turn_order isn't an active participant anymore (e.g. it
        # just died) — start from the first active participant instead.
        next_index = 0

    wrapped = next_index == 0
    next_participant = active[next_index]
    return TurnAdvanceResult(
        round=current_round + 1 if wrapped else current_round,
        turn_order=next_participant.turn_order,
        participant_id=next_participant.id,
    )
