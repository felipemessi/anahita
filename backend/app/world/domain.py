"""World-building domain enums and invariants (PRD §7.7)."""

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
