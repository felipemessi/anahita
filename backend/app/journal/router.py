"""HTTP router for the journal domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.journal.schemas import JournalEntryCreate, JournalEntryRead, JournalEntryUpdate
from app.journal.service import JournalService

router = APIRouter(tags=["journal"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_journal_service() -> JournalService:
    """Return a JournalService instance."""
    return JournalService()


JournalSvc = Annotated[JournalService, Depends(get_journal_service)]


@router.post(
    "/campaigns/{campaign_id}/journal",
    response_model=JournalEntryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_entry(
    campaign_id: uuid.UUID,
    body: JournalEntryCreate,
    user: CurrentUser,
    db: DB,
    service: JournalSvc,
) -> JournalEntryRead:
    """Create a journal entry; only the campaign's DM may do this."""
    entry = await service.create_entry(campaign_id, user.id, body, db)
    return JournalEntryRead.model_validate(entry)


@router.get("/campaigns/{campaign_id}/journal", response_model=list[JournalEntryRead])
async def list_entries(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: JournalSvc
) -> list[JournalEntryRead]:
    """List a campaign's journal entries, most recent first. DM-only."""
    entries = await service.list_entries(campaign_id, user.id, db)
    return [JournalEntryRead.model_validate(e) for e in entries]


@router.patch("/journal/{entry_id}", response_model=JournalEntryRead)
async def update_entry(
    entry_id: uuid.UUID,
    body: JournalEntryUpdate,
    user: CurrentUser,
    db: DB,
    service: JournalSvc,
) -> JournalEntryRead:
    """Update a journal entry's title/content/session link. DM-only."""
    entry = await service.update_entry(entry_id, user.id, body, db)
    return JournalEntryRead.model_validate(entry)


@router.delete("/journal/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entry(
    entry_id: uuid.UUID, user: CurrentUser, db: DB, service: JournalSvc
) -> None:
    """Delete a journal entry. DM-only."""
    await service.delete_entry(entry_id, user.id, db)
