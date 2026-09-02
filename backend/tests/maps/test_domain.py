"""Unit tests for app.maps.domain: token-kind validation and grid geometry."""

import uuid

import pytest

from app.maps.domain import (
    MapTokenKindError,
    cell_distance,
    feet_to_cells,
    validate_token_kind,
)


def test_validate_token_kind_accepts_exactly_one_or_none() -> None:
    """A single kind set, or none at all (manual token), is valid."""
    validate_token_kind(character_id=uuid.uuid4(), npc_id=None, monster_id=None)
    validate_token_kind(character_id=None, npc_id=uuid.uuid4(), monster_id=None)
    validate_token_kind(character_id=None, npc_id=None, monster_id=uuid.uuid4())
    validate_token_kind(character_id=None, npc_id=None, monster_id=None)


def test_validate_token_kind_rejects_more_than_one() -> None:
    """Setting both a character and a monster id is rejected."""
    with pytest.raises(MapTokenKindError):
        validate_token_kind(
            character_id=uuid.uuid4(), npc_id=None, monster_id=uuid.uuid4()
        )


def test_feet_to_cells_converts_at_five_feet_per_cell() -> None:
    """30ft of speed is 6 cells; a non-multiple-of-5 rounds down."""
    assert feet_to_cells(30) == 6
    assert feet_to_cells(25) == 5
    assert feet_to_cells(7) == 1


def test_cell_distance_is_chebyshev() -> None:
    """Diagonal movement costs the same as orthogonal — max(|dx|, |dy|)."""
    assert cell_distance(0, 0, 3, 0) == 3
    assert cell_distance(0, 0, 0, 4) == 4
    assert cell_distance(0, 0, 3, 3) == 3
    assert cell_distance(2, 2, 2, 2) == 0
