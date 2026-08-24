"""Inventory domain invariants (PRD §7.9)."""

import uuid


class LootDropKindError(ValueError):
    """Raised when a LootDrop's item reference is ambiguous or empty."""


def validate_loot_drop_kind(
    *,
    item_id: uuid.UUID | None,
    custom_item_name: str | None,
    currency_cp: int,
) -> None:
    """Enforce a LootDrop names at most one item, and drops *something*.

    `item_id` and `custom_item_name` are mutually exclusive (a drop is a
    catalog item **or** a free-text one, never both — same pattern as
    `app.combat.domain.validate_participant_kind`). A drop with neither and
    no currency has nothing to distribute, so it's rejected too.
    """
    if item_id is not None and custom_item_name is not None:
        raise LootDropKindError(
            "A loot drop cannot reference both a catalog item and a custom item name."
        )
    if item_id is None and custom_item_name is None and currency_cp <= 0:
        raise LootDropKindError(
            "A loot drop must have an item (catalog or custom) or "
            "a positive currency_cp."
        )
