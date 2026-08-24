"""HTTP router for the handouts domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.handouts.domain import HandoutType
from app.handouts.schemas import HandoutCreate, HandoutRead
from app.handouts.service import HandoutService
from app.storage import get_storage_service
from app.storage.base import StorageService

router = APIRouter(tags=["handouts"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_handout_service(
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> HandoutService:
    """Return a HandoutService wired to the configured StorageService."""
    return HandoutService(storage)


HandoutSvc = Annotated[HandoutService, Depends(get_handout_service)]


@router.post(
    "/campaigns/{campaign_id}/handouts",
    response_model=HandoutRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_handout(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: HandoutSvc,
    title: Annotated[str, Form()],
    handout_type: Annotated[HandoutType, Form()],
    content: Annotated[str | None, Form()] = None,
    session_id: Annotated[uuid.UUID | None, Form()] = None,
    file: UploadFile | None = None,
) -> HandoutRead:
    """Create a handout (text/image/map), optionally uploading a file. DM only."""
    file_bytes = await file.read() if file is not None else None
    return await service.create_handout(
        campaign_id,
        user.id,
        HandoutCreate(
            title=title,
            handout_type=handout_type,
            content=content,
            session_id=session_id,
        ),
        db,
        file_bytes=file_bytes,
        file_name=file.filename if file is not None else None,
        content_type=file.content_type if file is not None else None,
    )


@router.get("/campaigns/{campaign_id}/handouts", response_model=list[HandoutRead])
async def list_handouts(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: HandoutSvc,
) -> list[HandoutRead]:
    """List a campaign's handouts. Non-DM members only see revealed ones."""
    return await service.list_handouts(campaign_id, user.id, db)


@router.get("/handouts/{handout_id}", response_model=HandoutRead)
async def get_handout(
    handout_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: HandoutSvc,
) -> HandoutRead:
    """Get a handout's detail. Non-DM members can only see it if revealed."""
    return await service.get_handout(handout_id, user.id, db)


@router.post("/handouts/{handout_id}/reveal", response_model=HandoutRead)
async def reveal_handout(
    handout_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: HandoutSvc,
) -> HandoutRead:
    """Reveal a handout, broadcasting to any active encounter's session. DM only."""
    return await service.reveal_handout(handout_id, user.id, db)
