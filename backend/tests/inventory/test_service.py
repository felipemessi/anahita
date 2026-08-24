"""Integration tests for InventoryService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.inventory.schemas import (
    LootDropCreate,
    PartyInventoryCreate,
    PartyInventoryUpdate,
)
from app.inventory.service import InventoryService


async def test_dm_adds_and_lists_party_inventory(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """The DM adds an item stack; any campaign member can list it."""
    service = InventoryService()

    entry = await service.add_to_inventory(
        campaign_with_encounter.campaign_id,
        campaign_with_encounter.dm_id,
        PartyInventoryCreate(item_id=campaign_with_encounter.item_id, quantity=3),
        db,
    )
    assert entry.quantity == 3

    player_view = await service.list_inventory(
        campaign_with_encounter.campaign_id, campaign_with_encounter.player_id, db
    )
    assert len(player_view) == 1
    assert player_view[0].id == entry.id


async def test_player_cannot_add_to_inventory(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """A non-DM member is rejected when adding to the party inventory."""
    service = InventoryService()

    with pytest.raises(HTTPException) as exc_info:
        await service.add_to_inventory(
            campaign_with_encounter.campaign_id,
            campaign_with_encounter.player_id,
            PartyInventoryCreate(item_id=campaign_with_encounter.item_id),
            db,
        )
    assert exc_info.value.status_code == 403


async def test_dm_updates_and_removes_inventory_entry(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """The DM can adjust quantity/notes and remove an inventory entry."""
    service = InventoryService()
    entry = await service.add_to_inventory(
        campaign_with_encounter.campaign_id,
        campaign_with_encounter.dm_id,
        PartyInventoryCreate(item_id=campaign_with_encounter.item_id, quantity=1),
        db,
    )

    updated = await service.update_inventory_entry(
        campaign_with_encounter.campaign_id,
        entry.id,
        campaign_with_encounter.dm_id,
        PartyInventoryUpdate(quantity=5),
        db,
    )
    assert updated.quantity == 5

    await service.remove_from_inventory(
        campaign_with_encounter.campaign_id,
        entry.id,
        campaign_with_encounter.dm_id,
        db,
    )
    remaining = await service.list_inventory(
        campaign_with_encounter.campaign_id, campaign_with_encounter.dm_id, db
    )
    assert remaining == []


async def test_dm_creates_loot_drop_with_custom_item(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """The DM can drop a free-text (non-catalog) item after combat."""
    service = InventoryService()

    drop = await service.create_loot_drop(
        campaign_with_encounter.encounter_id,
        campaign_with_encounter.dm_id,
        LootDropCreate(custom_item_name="Rusty Dagger", quantity=1),
        db,
    )
    assert drop.custom_item_name == "Rusty Dagger"
    assert drop.item_id is None
    assert drop.claimed_by is None


async def test_dm_creates_loot_drop_with_pure_currency(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """The DM can drop pure currency with no item attached."""
    service = InventoryService()

    drop = await service.create_loot_drop(
        campaign_with_encounter.encounter_id,
        campaign_with_encounter.dm_id,
        LootDropCreate(currency_cp=1500),
        db,
    )
    assert drop.currency_cp == 1500
    assert drop.item_id is None
    assert drop.custom_item_name is None


async def test_loot_drop_rejects_item_and_custom_name_together(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """A loot drop can't name both a catalog item and a custom item name."""
    service = InventoryService()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_loot_drop(
            campaign_with_encounter.encounter_id,
            campaign_with_encounter.dm_id,
            LootDropCreate(
                item_id=campaign_with_encounter.item_id,
                custom_item_name="Rusty Dagger",
            ),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_loot_drop_rejects_empty_drop(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """A loot drop with no item and no currency is rejected."""
    service = InventoryService()

    with pytest.raises(HTTPException) as exc_info:
        await service.create_loot_drop(
            campaign_with_encounter.encounter_id,
            campaign_with_encounter.dm_id,
            LootDropCreate(),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_player_claims_loot_drop_for_own_character(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """A player can claim an unclaimed loot drop for their own character."""
    service = InventoryService()
    drop = await service.create_loot_drop(
        campaign_with_encounter.encounter_id,
        campaign_with_encounter.dm_id,
        LootDropCreate(item_id=campaign_with_encounter.item_id, quantity=1),
        db,
    )

    claimed = await service.claim_loot_drop(
        drop.id,
        campaign_with_encounter.player_id,
        campaign_with_encounter.character_id,
        db,
    )
    assert claimed.claimed_by == campaign_with_encounter.character_id


async def test_player_cannot_claim_loot_for_someone_elses_character(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """A player cannot claim a loot drop for a character they don't own."""
    service = InventoryService()
    drop = await service.create_loot_drop(
        campaign_with_encounter.encounter_id,
        campaign_with_encounter.dm_id,
        LootDropCreate(currency_cp=100),
        db,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.claim_loot_drop(
            drop.id, uuid.uuid4(), campaign_with_encounter.character_id, db
        )
    assert exc_info.value.status_code in (403, 404)


async def test_cannot_claim_already_claimed_drop(
    db: AsyncSession, campaign_with_encounter
) -> None:
    """Claiming an already-claimed loot drop is rejected."""
    service = InventoryService()
    drop = await service.create_loot_drop(
        campaign_with_encounter.encounter_id,
        campaign_with_encounter.dm_id,
        LootDropCreate(currency_cp=100),
        db,
    )
    await service.claim_loot_drop(
        drop.id,
        campaign_with_encounter.player_id,
        campaign_with_encounter.character_id,
        db,
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.claim_loot_drop(
            drop.id,
            campaign_with_encounter.dm_id,
            campaign_with_encounter.character_id,
            db,
        )
    assert exc_info.value.status_code == 409
