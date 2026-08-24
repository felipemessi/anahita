"""HTTP router for the timeline domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.dependencies import get_current_user
from app.database import get_db
from app.timeline.schemas import (
    TimelineEntryRead,
    TimelineEventCreate,
    TimelineEventRead,
    TimelineEventUpdate,
)
from app.timeline.service import TimelineService

router = APIRouter(tags=["timeline"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_timeline_service() -> TimelineService:
    """Return a TimelineService instance."""
    return TimelineService()


TimelineSvc = Annotated[TimelineService, Depends(get_timeline_service)]


@router.get(
    "/campaigns/{campaign_id}/timeline", response_model=list[TimelineEntryRead]
)
async def get_timeline(
    campaign_id: uuid.UUID, user: CurrentUser, db: DB, service: TimelineSvc
) -> list[TimelineEntryRead]:
    """Return a campaign's timeline: automatic session entries plus manual events."""
    entries = await service.get_timeline(campaign_id, user.id, db)
    return [TimelineEntryRead.model_validate(e, from_attributes=True) for e in entries]


@router.post(
    "/campaigns/{campaign_id}/timeline",
    response_model=TimelineEventRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_event(
    campaign_id: uuid.UUID,
    body: TimelineEventCreate,
    user: CurrentUser,
    db: DB,
    service: TimelineSvc,
) -> TimelineEventRead:
    """Create a manual timeline event; only the campaign's DM may do this."""
    event = await service.create_event(campaign_id, user.id, body, db)
    return TimelineEventRead.model_validate(event)


@router.patch("/timeline/{event_id}", response_model=TimelineEventRead)
async def update_event(
    event_id: uuid.UUID,
    body: TimelineEventUpdate,
    user: CurrentUser,
    db: DB,
    service: TimelineSvc,
) -> TimelineEventRead:
    """Update a manual timeline event; only the campaign's DM may do this."""
    event = await service.update_event(event_id, user.id, body, db)
    return TimelineEventRead.model_validate(event)


@router.delete("/timeline/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: uuid.UUID, user: CurrentUser, db: DB, service: TimelineSvc
) -> None:
    """Delete a manual timeline event; only the campaign's DM may do this."""
    await service.delete_event(event_id, user.id, db)
