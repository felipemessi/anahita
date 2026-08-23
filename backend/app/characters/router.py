"""HTTP router for the characters domain."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.characters.schemas import CharacterCreate, CharacterRead
from app.characters.service import CharacterService
from app.core.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/characters", tags=["characters"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_character_service() -> CharacterService:
    """Return a CharacterService instance."""
    return CharacterService()


@router.post("", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_character(
    body: CharacterCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CharacterService, Depends(get_character_service)],
) -> CharacterRead:
    """Create a character sheet for the authenticated user's own membership."""
    character = await service.create_character(user.id, body, db)
    return CharacterRead.model_validate(character)
