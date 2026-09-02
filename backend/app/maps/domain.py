"""Maps domain enums, invariants, and pure geometry (backlog Fase 15).

`app.maps` models a session's battle maps and the tokens positioned on
them — kept as its own domain (rather than folded into `app.sessions` or
`app.combat`) since it has its own lifecycle (a map outlives any one
encounter) while still linking into `app.combat.models.Encounter` for the
movement rule below.
"""

import uuid
from enum import StrEnum


class MapTokenKindError(ValueError):
    """Raised when a MapToken is linked to more than one of PC/NPC/monster."""


def validate_token_kind(
    *,
    character_id: uuid.UUID | None,
    npc_id: uuid.UUID | None,
    monster_id: uuid.UUID | None,
) -> None:
    """Enforce a token is a PC, an NPC, **or** a catalog monster — never more than one.

    None of the three being set is valid — a manual/generic token (e.g. a
    hazard marker), identified only by its `name` field. Mirrors
    `app.combat.domain.validate_participant_kind`.
    """
    kinds_set = sum(
        1 for kind_id in (character_id, npc_id, monster_id) if kind_id is not None
    )
    if kinds_set > 1:
        raise MapTokenKindError(
            "A map token can only be one of: a character, an NPC, or a catalog monster."
        )


class MoveOutOfRangeError(ValueError):
    """Raised when a move exceeds the mover's speed on their own combat turn."""


#: Feet per grid cell — fixed at 5ft (1.5m), matching the PRD's "grid de
#: 1,5m (5ft)" spec. Not configurable per map: `SessionMap.grid_size_px` is
#: only how many *pixels* one such cell spans in the uploaded image.
FEET_PER_CELL = 5


def feet_to_cells(feet: int) -> int:
    """Convert a speed in feet (`Character.speed`) to a whole number of cells.

    Rounds down — 5e speeds are always multiples of 5ft in practice, but a
    homebrew value that isn't still gets a safe (not overly generous) cell
    budget rather than raising.
    """
    return feet // FEET_PER_CELL


def cell_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """Distance in cells between two grid coordinates, diagonal included.

    Uses Chebyshev distance (`max(|dx|, |dy|)`) — every cell, including
    diagonals, costs one square of movement. This is a deliberate
    simplification of the PHB's default "5ft/10ft alternating diagonal"
    rule (which is path-dependent, not just start/end coordinates); it
    matches the flat-cost optional rule most virtual tabletops use, and
    this app only knows a token's start and end cell, not the path it
    walked between them.
    """
    return max(abs(x2 - x1), abs(y2 - y1))


class MapVisibility(StrEnum):
    """Whether a token is visible to players, or DM-only (a hidden NPC/monster)."""

    visible = "visible"
    hidden = "hidden"
