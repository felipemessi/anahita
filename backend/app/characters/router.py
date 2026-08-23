"""HTTP router for the characters domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.characters.schemas import (
    CharacterClassCreate,
    CharacterCreate,
    CharacterRead,
    CharacterUpdate,
)
from app.characters.service import CharacterService
from app.core.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/characters", tags=["characters"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_character_service() -> CharacterService:
    """Return a CharacterService instance."""
    return CharacterService()


@router.get("", response_model=list[CharacterRead])
async def list_characters(
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    campaign_id: Annotated[uuid.UUID, Query()],
) -> list[CharacterRead]:
    """List every character in a campaign. Viewable by any of its members."""
    return await service.list_characters_for_campaign(campaign_id, user.id, db)


@router.post("", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Create a character sheet for the authenticated user's own membership."""
    return await service.create_character(user.id, body, db)


@router.get("/{character_id}", response_model=CharacterRead)
async def get_character(
    character_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Fetch a character sheet with calculated modifiers and skill bonuses."""
    return await service.get_character(character_id, user.id, db)


@router.post("/{character_id}/classes", response_model=CharacterRead)
async def add_class(
    character_id: uuid.UUID,
    body: CharacterClassCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Add a class to a character, enabling multiclass (PHB ability score rules)."""
    return await service.add_class(character_id, user.id, body, db)


@router.patch("/{character_id}", response_model=CharacterRead)
async def update_character(
    character_id: uuid.UUID,
    body: CharacterUpdate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Update a character's combat-facing fields (HP/AC/inspiration). Owner only."""
    return await service.update_character(character_id, user.id, body, db)
