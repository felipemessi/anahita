"""HTTP router for the characters domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.catalog.schemas import FeatureRead
from app.characters.schemas import (
    CharacterClassCreate,
    CharacterConcentrationRequest,
    CharacterCreate,
    CharacterCurrencyRequest,
    CharacterDeathSaveRequest,
    CharacterDeathSaveResponse,
    CharacterEquipmentCreate,
    CharacterEquipmentUpdate,
    CharacterFeatureCreate,
    CharacterLevelUpRequest,
    CharacterProficiencyChoiceRequest,
    CharacterRead,
    CharacterRestRequest,
    CharacterRestResponse,
    CharacterSpellCastRequest,
    CharacterSpellCastResponse,
    CharacterSpellCreate,
    CharacterSpellUpdate,
    CharacterSummaryRead,
    CharacterUpdate,
    SpellAttackProfileRead,
    WeaponAttackProfileRead,
)
from app.characters.service import CharacterService
from app.core.dependencies import get_current_user
from app.database import get_db
from app.storage import get_storage_service
from app.storage.base import StorageService

router = APIRouter(prefix="/characters", tags=["characters"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_character_service(
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> CharacterService:
    """Return a CharacterService wired to the configured StorageService."""
    return CharacterService(storage)


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


@router.post("/{character_id}/level-up", response_model=CharacterRead)
async def level_up(
    character_id: uuid.UUID,
    body: CharacterLevelUpRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Level up a character by one level in one class. Owner only."""
    return await service.level_up(character_id, user.id, body, db)


@router.post("/{character_id}/proficiencies", response_model=CharacterRead)
async def set_proficiency_choices(
    character_id: uuid.UUID,
    body: CharacterProficiencyChoiceRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Mark chosen skills proficient, restricted to the character's valid choice set."""
    return await service.set_proficiency_choices(character_id, user.id, body, db)


@router.get(
    "/{character_id}/resources/{resource_key}/options",
    response_model=list[FeatureRead],
)
async def get_resource_options(
    character_id: uuid.UUID,
    resource_key: str,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    locale: Annotated[
        str, Query(description="Locale for translated text (en, pt-BR)")
    ] = "en",
) -> list[FeatureRead]:
    """List the named options for a class resource (e.g. Channel Divinity).

    Owner only.
    """
    return await service.get_resource_options(
        character_id, user.id, resource_key, db, locale=locale
    )


@router.post(
    "/{character_id}/resources/{resource_key}/use", response_model=CharacterRead
)
async def use_resource(
    character_id: uuid.UUID,
    resource_key: str,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    option_id: Annotated[
        uuid.UUID | None,
        Query(description="Which named option this use spent, if more than one"),
    ] = None,
) -> CharacterRead:
    """Spend one use of a class resource (rage, ki, ...). Owner only."""
    return await service.use_resource(
        character_id, user.id, resource_key, db, option_id=option_id
    )


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


@router.post("/{character_id}/portrait", response_model=CharacterRead)
async def upload_portrait(
    character_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    file: UploadFile,
) -> CharacterRead:
    """Set (or replace) a character's portrait image. Owner only."""
    file_bytes = await file.read()
    return await service.upload_portrait(
        character_id,
        user.id,
        db,
        file_bytes=file_bytes,
        file_name=file.filename,
        content_type=file.content_type,
    )


@router.delete("/{character_id}/portrait", response_model=CharacterRead)
async def remove_portrait(
    character_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Remove a character's portrait, reverting to the imageless state. Owner only."""
    return await service.remove_portrait(character_id, user.id, db)


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


@router.post(
    "/{character_id}/spells/{spell_id}/cast",
    response_model=CharacterSpellCastResponse,
)
async def cast_spell(
    character_id: uuid.UUID,
    spell_id: uuid.UUID,
    body: CharacterSpellCastRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterSpellCastResponse:
    """Cast a known spell, consuming a spell slot. Owner only."""
    return await service.cast_spell(character_id, spell_id, user.id, body, db)


@router.get(
    "/{character_id}/spells/{spell_id}/attack-profile",
    response_model=SpellAttackProfileRead,
)
async def get_spell_attack_profile(
    character_id: uuid.UUID,
    spell_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
    cast_at_level: int | None = None,
) -> SpellAttackProfileRead:
    """Resolve a known spell into its attack/save + damage roll profile. Owner only."""
    return await service.get_spell_attack_profile(
        character_id, spell_id, cast_at_level, user.id, db
    )


@router.post("/{character_id}/rest", response_model=CharacterRestResponse)
async def rest(
    character_id: uuid.UUID,
    body: CharacterRestRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRestResponse:
    """Take a short or long rest. Owner only."""
    return await service.rest(character_id, user.id, body, db)


@router.post("/{character_id}/death-save", response_model=CharacterDeathSaveResponse)
async def death_save(
    character_id: uuid.UUID,
    body: CharacterDeathSaveRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterDeathSaveResponse:
    """Roll a death saving throw. Owner only, only at 0 hit points."""
    return await service.death_save(character_id, user.id, body, db)


@router.post("/{character_id}/concentration", response_model=CharacterRead)
async def set_concentration(
    character_id: uuid.UUID,
    body: CharacterConcentrationRequest,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Start or end concentration on a known spell. Owner only."""
    return await service.set_concentration(character_id, user.id, body, db)


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


@router.get(
    "/{character_id}/equipment/{equipment_id}/attack-profile",
    response_model=WeaponAttackProfileRead,
)
async def get_weapon_attack_profile(
    character_id: uuid.UUID,
    equipment_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> WeaponAttackProfileRead:
    """Resolve an equipped weapon into an attack bonus + damage roll. Owner only."""
    return await service.get_weapon_attack_profile(
        character_id, equipment_id, user.id, db
    )


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
