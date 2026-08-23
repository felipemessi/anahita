"""Campaigns domain enums and invariants."""

from enum import StrEnum


class CampaignStatus(StrEnum):
    """Lifecycle status of a campaign."""

    active = "active"
    paused = "paused"
    archived = "archived"


class CampaignRole(StrEnum):
    """A member's role within a campaign."""

    dm = "dm"
    player = "player"
