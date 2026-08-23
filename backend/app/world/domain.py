"""World-building domain enums and invariants (PRD §7.7)."""

import uuid
from enum import StrEnum


class LocationType(StrEnum):
    """The kind of place a Location represents."""

    city = "city"
    town = "town"
    dungeon = "dungeon"
    wilderness = "wilderness"
    building = "building"
    region = "region"
    plane = "plane"


class NPCLocationPresenceType(StrEnum):
    """How an NPC relates to a Location they're linked to."""

    resides = "resides"
    frequents = "frequents"
    controls = "controls"


class FactionRelationshipType(StrEnum):
    """How two Factions relate to each other."""

    allied = "allied"
    hostile = "hostile"
    neutral = "neutral"
    vassal = "vassal"
    trade_partner = "trade_partner"


class LocationCycleError(ValueError):
    """Raised when reparenting a Location would create a cycle in the hierarchy."""


def validate_no_parent_cycle(
    *,
    location_id: uuid.UUID,
    new_parent_id: uuid.UUID | None,
    new_parent_ancestor_ids: set[uuid.UUID],
) -> None:
    """Reject a reparent that would make `location_id` its own ancestor.

    `new_parent_ancestor_ids` is the chain of parents above `new_parent_id`
    (inclusive of `new_parent_id` itself), walked by the caller before this
    is invoked — a pure check keeps the cycle rule testable without a DB.
    """
    if new_parent_id is None:
        return
    if new_parent_id == location_id or location_id in new_parent_ancestor_ids:
        raise LocationCycleError(
            "Cannot set this parent — it would create a cycle in the location hierarchy"
        )
