"""HTTP router for the world-building domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.world.schemas import (
    FactionCreate,
    FactionRead,
    LocationCreate,
    LocationParentUpdate,
    LocationRead,
    LocationTreeNode,
    NPCCreate,
    NPCRead,
)
from app.world.service import WorldService

router = APIRouter(tags=["world"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_world_service() -> WorldService:
    """Return a WorldService instance."""
    return WorldService()


WorldSvc = Annotated[WorldService, Depends(get_world_service)]


@router.post(
    "/campaigns/{campaign_id}/npcs",
    response_model=NPCRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_npc(
    campaign_id: uuid.UUID,
    body: NPCCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> NPCRead:
    """Create an NPC for a campaign; only the campaign's DM may do this."""
    npc = await service.create_npc(campaign_id, user.id, body, db)
    return NPCRead.model_validate(npc)


@router.get("/campaigns/{campaign_id}/npcs", response_model=list[NPCRead])
async def list_npcs(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[NPCRead]:
    """List a campaign's NPCs."""
    npcs = await service.list_npcs(campaign_id, user.id, db)
    return [NPCRead.model_validate(n) for n in npcs]


@router.post(
    "/campaigns/{campaign_id}/locations",
    response_model=LocationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_location(
    campaign_id: uuid.UUID,
    body: LocationCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> LocationRead:
    """Create a location for a campaign; only the campaign's DM may do this."""
    location = await service.create_location(campaign_id, user.id, body, db)
    return LocationRead.model_validate(location)


@router.get("/campaigns/{campaign_id}/locations", response_model=list[LocationRead])
async def list_locations(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[LocationRead]:
    """List a campaign's locations."""
    locations = await service.list_locations(campaign_id, user.id, db)
    return [LocationRead.model_validate(loc) for loc in locations]


@router.patch("/locations/{location_id}/parent", response_model=LocationRead)
async def update_location_parent(
    location_id: uuid.UUID,
    body: LocationParentUpdate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> LocationRead:
    """Reparent a location; rejects any change that would create a cycle."""
    location = await service.update_location_parent(location_id, user.id, body, db)
    return LocationRead.model_validate(location)


@router.get(
    "/campaigns/{campaign_id}/locations/tree", response_model=list[LocationTreeNode]
)
async def get_location_tree(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[LocationTreeNode]:
    """Return a campaign's locations nested by parent, root locations first."""
    return await service.get_location_tree(campaign_id, user.id, db)


@router.post(
    "/campaigns/{campaign_id}/factions",
    response_model=FactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_faction(
    campaign_id: uuid.UUID,
    body: FactionCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> FactionRead:
    """Create a faction for a campaign; only the campaign's DM may do this."""
    faction = await service.create_faction(campaign_id, user.id, body, db)
    return FactionRead.model_validate(faction)


@router.get("/campaigns/{campaign_id}/factions", response_model=list[FactionRead])
async def list_factions(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[FactionRead]:
    """List a campaign's factions."""
    factions = await service.list_factions(campaign_id, user.id, db)
    return [FactionRead.model_validate(f) for f in factions]
