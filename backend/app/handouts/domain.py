"""Handouts domain enums (PRD §7.8)."""

from enum import StrEnum


class HandoutType(StrEnum):
    """The kind of content a Handout carries."""

    text = "text"
    image = "image"
    map = "map"
