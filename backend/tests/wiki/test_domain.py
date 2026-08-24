"""Unit tests for `app.wiki.domain` pure helpers."""

import uuid

import pytest

from app.wiki.domain import WikiPageLinkKindError, slugify, validate_wiki_link_kind


def test_slugify_lowercases_and_hyphenates() -> None:
    """A normal title becomes a lowercase, hyphen-separated slug."""
    assert slugify("The Sunken Temple") == "the-sunken-temple"


def test_slugify_strips_punctuation() -> None:
    """Non-alphanumeric characters collapse into single hyphens."""
    assert slugify("Volo's Guide: Monsters!") == "volo-s-guide-monsters"


def test_slugify_falls_back_when_title_has_no_alnum_chars() -> None:
    """A title with nothing slug-worthy still produces a usable slug."""
    assert slugify("***") == "page"


def test_allows_exactly_one_target() -> None:
    """A link with exactly one of npc/location/faction is fine."""
    validate_wiki_link_kind(npc_id=uuid.uuid4(), location_id=None, faction_id=None)
    validate_wiki_link_kind(npc_id=None, location_id=uuid.uuid4(), faction_id=None)
    validate_wiki_link_kind(npc_id=None, location_id=None, faction_id=uuid.uuid4())


def test_rejects_no_target() -> None:
    """A link with no target has nothing to point at."""
    with pytest.raises(WikiPageLinkKindError):
        validate_wiki_link_kind(npc_id=None, location_id=None, faction_id=None)


def test_rejects_more_than_one_target() -> None:
    """A link with two targets set is ambiguous."""
    with pytest.raises(WikiPageLinkKindError):
        validate_wiki_link_kind(
            npc_id=uuid.uuid4(), location_id=uuid.uuid4(), faction_id=None
        )
