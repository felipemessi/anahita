"""HTTP router for the characters domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.characters.schemas import (
    CharacterClassCreate,
    CharacterCreate,
    CharacterCurrencyRequest,
    CharacterEquipmentCreate,
    CharacterEquipmentUpdate,
    CharacterFeatureCreate,
    CharacterRead,
    CharacterRestRequest,
    CharacterSpellCastRequest,
    CharacterSpellCreate,
    CharacterSpellUpdate,
    CharacterSummaryRead,
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


@router.get("", response_model=list[CharacterRead | CharacterSummaryRead])
async def list_characters(
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    campaign_id: Annotated[uuid.UUID, Query()],
) -> list[CharacterRead | CharacterSummaryRead]:
    """List every character in a campaign. Viewable by any of its members.

    The owner and the DM get the full sheet; other members get a summary.
    """
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


@router.post("/{character_id}/spells", response_model=CharacterRead)
async def add_spell(
    character_id: uuid.UUID,
    body: CharacterSpellCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Add a known/prepared spell to a character. Owner only."""
    return await service.add_spell(character_id, user.id, body, db)


@router.patch("/{character_id}/spells/{spell_id}", response_model=CharacterRead)
async def update_spell(
    character_id: uuid.UUID,
    spell_id: uuid.UUID,
    body: CharacterSpellUpdate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Toggle a known spell's `prepared` flag. Owner only."""
    return await service.update_spell(character_id, spell_id, user.id, body, db)


@router.delete("/{character_id}/spells/{spell_id}", response_model=CharacterRead)
async def remove_spell(
    character_id: uuid.UUID,
    spell_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Forget a known spell. Owner only."""
    return await service.remove_spell(character_id, spell_id, user.id, db)


@router.post("/{character_id}/spells/{spell_id}/cast", response_model=CharacterRead)
async def cast_spell(
    character_id: uuid.UUID,
    spell_id: uuid.UUID,
    body: CharacterSpellCastRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Cast a known spell, consuming a spell slot. Owner only."""
    return await service.cast_spell(character_id, spell_id, user.id, body, db)


@router.post("/{character_id}/rest", response_model=CharacterRead)
async def rest(
    character_id: uuid.UUID,
    body: CharacterRestRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Take a short or long rest. Owner only."""
    return await service.rest(character_id, user.id, body, db)


@router.post("/{character_id}/equipment", response_model=CharacterRead)
async def add_equipment(
    character_id: uuid.UUID,
    body: CharacterEquipmentCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Add an item to a character's personal inventory. Owner only."""
    return await service.add_equipment(character_id, user.id, body, db)


@router.patch("/{character_id}/equipment/{equipment_id}", response_model=CharacterRead)
async def update_equipment(
    character_id: uuid.UUID,
    equipment_id: uuid.UUID,
    body: CharacterEquipmentUpdate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Edit an inventory item (equipped/attunement/quantity). Owner only."""
    return await service.update_equipment(character_id, equipment_id, user.id, body, db)


@router.delete("/{character_id}/equipment/{equipment_id}", response_model=CharacterRead)
async def remove_equipment(
    character_id: uuid.UUID,
    equipment_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Remove an item from a character's inventory. Owner only."""
    return await service.remove_equipment(character_id, equipment_id, user.id, db)


@router.post("/{character_id}/currency", response_model=CharacterRead)
async def update_currency(
    character_id: uuid.UUID,
    body: CharacterCurrencyRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Record a currency gain (positive `delta`) or spend (negative). Owner only."""
    return await service.update_currency(character_id, user.id, body, db)


@router.post("/{character_id}/features", response_model=CharacterRead)
async def add_feature(
    character_id: uuid.UUID,
    body: CharacterFeatureCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Record a class/feat feature on a character. Owner only."""
    return await service.add_feature(character_id, user.id, body, db)
