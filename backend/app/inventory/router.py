"""HTTP router for the inventory domain: party inventory and loot drops."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.inventory.schemas import (
    LootDropClaim,
    LootDropCreate,
    LootDropRead,
    PartyInventoryCreate,
    PartyInventoryRead,
    PartyInventoryUpdate,
)
from app.inventory.service import InventoryService

router = APIRouter(tags=["inventory"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_inventory_service() -> InventoryService:
    """Return an InventoryService instance."""
    return InventoryService()


InventorySvc = Annotated[InventoryService, Depends(get_inventory_service)]


@router.post(
    "/campaigns/{campaign_id}/inventory",
    response_model=PartyInventoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_to_inventory(
    campaign_id: uuid.UUID,
    body: PartyInventoryCreate,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> PartyInventoryRead:
    """Add a stack of an item to the party inventory. DM only."""
    return await service.add_to_inventory(campaign_id, user.id, body, db)


@router.get(
    "/campaigns/{campaign_id}/inventory", response_model=list[PartyInventoryRead]
)
async def list_inventory(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> list[PartyInventoryRead]:
    """List a campaign's party inventory. Viewable by any campaign member."""
    return await service.list_inventory(campaign_id, user.id, db)


@router.patch(
    "/campaigns/{campaign_id}/inventory/{entry_id}",
    response_model=PartyInventoryRead,
)
async def update_inventory_entry(
    campaign_id: uuid.UUID,
    entry_id: uuid.UUID,
    body: PartyInventoryUpdate,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> PartyInventoryRead:
    """Update a party inventory entry's quantity/notes. DM only."""
    return await service.update_inventory_entry(
        campaign_id, entry_id, user.id, body, db
    )


@router.delete(
    "/campaigns/{campaign_id}/inventory/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_from_inventory(
    campaign_id: uuid.UUID,
    entry_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> None:
    """Remove a party inventory entry entirely. DM only."""
    await service.remove_from_inventory(campaign_id, entry_id, user.id, db)


@router.post(
    "/encounters/{encounter_id}/loot",
    response_model=LootDropRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_loot_drop(
    encounter_id: uuid.UUID,
    body: LootDropCreate,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> LootDropRead:
    """Record a loot drop for an encounter (item and/or currency). DM only."""
    return await service.create_loot_drop(encounter_id, user.id, body, db)


@router.get("/encounters/{encounter_id}/loot", response_model=list[LootDropRead])
async def list_loot_drops(
    encounter_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> list[LootDropRead]:
    """List an encounter's loot drops. Viewable by any campaign member."""
    return await service.list_loot_drops(encounter_id, user.id, db)


@router.post("/loot-drops/{loot_drop_id}/claim", response_model=LootDropRead)
async def claim_loot_drop(
    loot_drop_id: uuid.UUID,
    body: LootDropClaim,
    user: CurrentUser,
    db: DB,
    service: InventorySvc,
) -> LootDropRead:
    """Claim a loot drop for a character. The character's own player, or the DM."""
    return await service.claim_loot_drop(loot_drop_id, user.id, body.character_id, db)
