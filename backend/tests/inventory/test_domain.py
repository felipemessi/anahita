"""Unit tests for `app.inventory.domain.validate_loot_drop_kind`."""

import uuid

import pytest

from app.inventory.domain import LootDropKindError, validate_loot_drop_kind


def test_allows_pure_currency() -> None:
    """No item reference at all is fine as long as there's currency."""
    validate_loot_drop_kind(
        item_id=None, magic_item_id=None, custom_item_name=None, currency_cp=100
    )


def test_allows_single_catalog_item() -> None:
    """A single catalog item reference, with or without currency, is fine."""
    validate_loot_drop_kind(
        item_id=uuid.uuid4(),
        magic_item_id=None,
        custom_item_name=None,
        currency_cp=0,
    )


def test_allows_single_magic_item() -> None:
    """A single magic item reference is fine."""
    validate_loot_drop_kind(
        item_id=None,
        magic_item_id=uuid.uuid4(),
        custom_item_name=None,
        currency_cp=0,
    )


def test_allows_single_custom_name() -> None:
    """A single custom item name is fine."""
    validate_loot_drop_kind(
        item_id=None,
        magic_item_id=None,
        custom_item_name="Rusty Dagger",
        currency_cp=0,
    )


def test_rejects_item_and_magic_item_together() -> None:
    """A catalog item and a magic item can't both be set."""
    with pytest.raises(LootDropKindError):
        validate_loot_drop_kind(
            item_id=uuid.uuid4(),
            magic_item_id=uuid.uuid4(),
            custom_item_name=None,
            currency_cp=0,
        )


def test_rejects_magic_item_and_custom_name_together() -> None:
    """A magic item and a custom name can't both be set."""
    with pytest.raises(LootDropKindError):
        validate_loot_drop_kind(
            item_id=None,
            magic_item_id=uuid.uuid4(),
            custom_item_name="Rusty Dagger",
            currency_cp=0,
        )


def test_rejects_empty_drop() -> None:
    """No item reference and no currency has nothing to distribute."""
    with pytest.raises(LootDropKindError):
        validate_loot_drop_kind(
            item_id=None, magic_item_id=None, custom_item_name=None, currency_cp=0
        )
