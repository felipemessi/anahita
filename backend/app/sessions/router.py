"""HTTP router for the sessions domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.sessions.schemas import (
    SessionCreate,
    SessionNoteCreate,
    SessionNoteRead,
    SessionRead,
)
from app.sessions.service import SessionService

router = APIRouter(tags=["sessions"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_session_service() -> SessionService:
    """Return a SessionService instance."""
    return SessionService()


@router.post(
    "/campaigns/{campaign_id}/sessions",
    response_model=SessionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(
    campaign_id: uuid.UUID,
    body: SessionCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionRead:
    """Create a session for a campaign; only the campaign's DM may do this."""
    session = await service.create_session(campaign_id, user.id, body, db)
    return SessionRead.model_validate(session)


@router.get("/campaigns/{campaign_id}/sessions", response_model=list[SessionRead])
async def list_sessions(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> list[SessionRead]:
    """List a campaign's sessions; `dm_notes` is only populated for the DM."""
    return await service.list_sessions(campaign_id, user.id, db)


@router.post(
    "/sessions/{session_id}/notes",
    response_model=SessionNoteRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_note(
    session_id: uuid.UUID,
    body: SessionNoteCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> SessionNoteRead:
    """Add a note to a session; only the DM may mark a note private."""
    note = await service.add_note(session_id, user.id, body, db)
    return SessionNoteRead.model_validate(note)


@router.get("/sessions/{session_id}/notes", response_model=list[SessionNoteRead])
async def list_notes(
    session_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[SessionService, Depends(get_session_service)],
) -> list[SessionNoteRead]:
    """List a session's notes; the DM sees private notes, other members don't."""
    notes = await service.list_notes(session_id, user.id, db)
    return [SessionNoteRead.model_validate(n) for n in notes]
