"""Wiki domain invariants and pure helpers (PRD §7.10)."""

import re
import uuid

_SLUG_INVALID_CHARS = re.compile(r"[^a-z0-9]+")


def slugify(title: str) -> str:
    """Turn a page title into a URL-safe slug: lowercase, hyphen-separated.

    Not guaranteed unique on its own — the service layer appends a numeric
    suffix on collision within the same campaign.
    """
    slug = _SLUG_INVALID_CHARS.sub("-", title.strip().lower()).strip("-")
    return slug or "page"


class WikiPageLinkKindError(ValueError):
    """Raised when a WikiPageLink's target reference is ambiguous or empty."""


def validate_wiki_link_kind(
    *,
    npc_id: uuid.UUID | None,
    location_id: uuid.UUID | None,
    faction_id: uuid.UUID | None,
) -> None:
    """Enforce a WikiPageLink points at exactly one target.

    `npc_id`, `location_id`, and `faction_id` are mutually exclusive — same
    pattern as `app.inventory.domain.validate_loot_drop_kind` — and exactly
    one must be set, since a link with none has nothing to point at.
    """
    kinds_set = sum(1 for kind in (npc_id, location_id, faction_id) if kind is not None)
    if kinds_set != 1:
        raise WikiPageLinkKindError(
            "A wiki page link must reference exactly one of: an NPC, a "
            "location, or a faction."
        )
