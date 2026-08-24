"""Inventory domain invariants (PRD §7.9)."""

import uuid


class LootDropKindError(ValueError):
    """Raised when a LootDrop's item reference is ambiguous or empty."""


def validate_loot_drop_kind(
    *,
    item_id: uuid.UUID | None,
    magic_item_id: uuid.UUID | None,
    custom_item_name: str | None,
    currency_cp: int,
) -> None:
    """Enforce a LootDrop names at most one item, and drops *something*.

    `item_id`, `magic_item_id`, and `custom_item_name` are mutually exclusive
    (a drop is a catalog item, a magic item, **or** a free-text one, never
    more than one — same pattern as `app.combat.domain.
    validate_participant_kind`). A drop with none of the three and no
    currency has nothing to distribute, so it's rejected too.
    """
    kinds_set = sum(
        1 for kind in (item_id, magic_item_id, custom_item_name) if kind is not None
    )
    if kinds_set > 1:
        raise LootDropKindError(
            "A loot drop can reference at most one of: a catalog item, "
            "a magic item, or a custom item name."
        )
    if kinds_set == 0 and currency_cp <= 0:
        raise LootDropKindError(
            "A loot drop must have an item (catalog, magic, or custom) or "
            "a positive currency_cp."
        )
