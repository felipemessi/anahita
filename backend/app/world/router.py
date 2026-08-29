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
    FactionRelationshipCreate,
    FactionRelationshipRead,
    LocationCreate,
    LocationParentUpdate,
    LocationRead,
    LocationSessionCreate,
    LocationSessionRead,
    LocationTreeNode,
    NPCCreate,
    NPCFactionCreate,
    NPCFactionRead,
    NPCLocationCreate,
    NPCLocationRead,
    NPCRead,
    NPCSessionCreate,
    NPCSessionRead,
    WorldSearchResult,
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
    """List a campaign's NPCs. Non-DM members only see revealed ones."""
    npcs = await service.list_npcs(campaign_id, user.id, db)
    return [NPCRead.model_validate(n) for n in npcs]


@router.get("/npcs/{npc_id}", response_model=NPCRead)
async def get_npc(
    npc_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> NPCRead:
    """Get an NPC's detail. Non-DM members can only see it if revealed."""
    npc = await service.get_npc(npc_id, user.id, db)
    return NPCRead.model_validate(npc)


@router.post("/npcs/{npc_id}/reveal", response_model=NPCRead)
async def reveal_npc(
    npc_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> NPCRead:
    """Reveal an NPC to players. DM-only."""
    npc = await service.reveal_npc(npc_id, user.id, db)
    return NPCRead.model_validate(npc)


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


@router.get(
    "/campaigns/{campaign_id}/world/search", response_model=list[WorldSearchResult]
)
async def search_world(
    campaign_id: uuid.UUID,
    q: str,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> list[WorldSearchResult]:
    """Search a campaign's NPCs, locations, and factions by name/description."""
    return await service.search(campaign_id, user.id, q, db)


@router.post(
    "/npcs/{npc_id}/factions",
    response_model=NPCFactionRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_npc_faction(
    npc_id: uuid.UUID,
    body: NPCFactionCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> NPCFactionRead:
    """Link an NPC to a faction from their own campaign; DM-only."""
    link = await service.link_npc_faction(npc_id, user.id, body, db)
    return NPCFactionRead.model_validate(link)


@router.get("/npcs/{npc_id}/factions", response_model=list[NPCFactionRead])
async def list_npc_factions(
    npc_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[NPCFactionRead]:
    """List an NPC's faction links."""
    links = await service.list_npc_factions(npc_id, user.id, db)
    return [NPCFactionRead.model_validate(link) for link in links]


@router.post(
    "/npcs/{npc_id}/locations",
    response_model=NPCLocationRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_npc_location(
    npc_id: uuid.UUID,
    body: NPCLocationCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> NPCLocationRead:
    """Link an NPC to a location from their own campaign; DM-only."""
    link = await service.link_npc_location(npc_id, user.id, body, db)
    return NPCLocationRead.model_validate(link)


@router.get("/npcs/{npc_id}/locations", response_model=list[NPCLocationRead])
async def list_npc_locations(
    npc_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[NPCLocationRead]:
    """List an NPC's location links."""
    links = await service.list_npc_locations(npc_id, user.id, db)
    return [NPCLocationRead.model_validate(link) for link in links]


@router.post(
    "/npcs/{npc_id}/sessions",
    response_model=NPCSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_npc_session(
    npc_id: uuid.UUID,
    body: NPCSessionCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> NPCSessionRead:
    """Link an NPC to a session appearance from their own campaign; DM-only."""
    link = await service.link_npc_session(npc_id, user.id, body, db)
    return NPCSessionRead.model_validate(link)


@router.get("/npcs/{npc_id}/sessions", response_model=list[NPCSessionRead])
async def list_npc_sessions(
    npc_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[NPCSessionRead]:
    """List an NPC's session appearances."""
    links = await service.list_npc_sessions(npc_id, user.id, db)
    return [NPCSessionRead.model_validate(link) for link in links]


@router.post(
    "/locations/{location_id}/sessions",
    response_model=LocationSessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_location_session(
    location_id: uuid.UUID,
    body: LocationSessionCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> LocationSessionRead:
    """Link a location to a session visit from their own campaign; DM-only."""
    link = await service.link_location_session(location_id, user.id, body, db)
    return LocationSessionRead.model_validate(link)


@router.get(
    "/locations/{location_id}/sessions", response_model=list[LocationSessionRead]
)
async def list_location_sessions(
    location_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[LocationSessionRead]:
    """List a location's session visits."""
    links = await service.list_location_sessions(location_id, user.id, db)
    return [LocationSessionRead.model_validate(link) for link in links]


@router.post(
    "/factions/{faction_id}/relationships",
    response_model=FactionRelationshipRead,
    status_code=status.HTTP_201_CREATED,
)
async def link_faction_relationship(
    faction_id: uuid.UUID,
    body: FactionRelationshipCreate,
    user: CurrentUser,
    db: DB,
    service: WorldSvc,
) -> FactionRelationshipRead:
    """Set a relationship between two factions from the same campaign; DM-only."""
    link = await service.link_faction_relationship(faction_id, user.id, body, db)
    return FactionRelationshipRead.model_validate(link)


@router.get(
    "/factions/{faction_id}/relationships", response_model=list[FactionRelationshipRead]
)
async def list_faction_relationships(
    faction_id: uuid.UUID, user: CurrentUser, db: DB, service: WorldSvc
) -> list[FactionRelationshipRead]:
    """List a faction's relationships (as either side)."""
    links = await service.list_faction_relationships(faction_id, user.id, db)
    return [FactionRelationshipRead.model_validate(link) for link in links]
