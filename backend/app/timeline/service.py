"""TimelineService orchestrates manual timeline events and the fused read."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.queries.timeline_queries import TimelineEntry, get_campaign_timeline
from app.sessions.models import Session
from app.timeline.models import TimelineEvent
from app.timeline.schemas import TimelineEventCreate, TimelineEventUpdate


class TimelineService:
    """Orchestrates manual TimelineEvent CRUD and the fused timeline read."""

    async def get_timeline(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[TimelineEntry]:
        """Return a campaign's fused timeline; requester must be a member."""
        await self._require_membership(campaign_id, requester_id, db)
        return await get_campaign_timeline(campaign_id, db)

    async def create_event(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: TimelineEventCreate,
        db: AsyncSession,
    ) -> TimelineEvent:
        """Create a manual timeline event; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)
        if data.session_id is not None:
            await self._require_same_campaign_session(data.session_id, campaign_id, db)

        event = TimelineEvent(
            campaign_id=campaign_id,
            title=data.title,
            description=data.description,
            session_id=data.session_id,
            in_game_date=data.in_game_date,
            sort_order=data.sort_order,
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def update_event(
        self,
        event_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: TimelineEventUpdate,
        db: AsyncSession,
    ) -> TimelineEvent:
        """Update a manual timeline event; only the campaign's DM may do this."""
        event = await self._require_event(event_id, db)
        await self._require_dm(event.campaign_id, requester_id, db)

        if data.title is not None:
            event.title = data.title
        if data.description is not None:
            event.description = data.description
        if data.session_id is not None:
            await self._require_same_campaign_session(
                data.session_id, event.campaign_id, db
            )
            event.session_id = data.session_id
        if data.in_game_date is not None:
            event.in_game_date = data.in_game_date
        if data.sort_order is not None:
            event.sort_order = data.sort_order
        await db.commit()
        await db.refresh(event)
        return event

    async def delete_event(
        self, event_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Delete a manual timeline event; only the campaign's DM may do this."""
        event = await self._require_event(event_id, db)
        await self._require_dm(event.campaign_id, requester_id, db)
        await db.delete(event)
        await db.commit()

    async def _require_event(
        self, event_id: uuid.UUID, db: AsyncSession
    ) -> TimelineEvent:
        """Fetch a manual timeline event by id, or raise 404."""
        result = await db.execute(
            select(TimelineEvent).where(TimelineEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Timeline event not found"
            )
        return event

    async def _require_same_campaign_session(
        self, session_id: uuid.UUID, campaign_id: uuid.UUID, db: AsyncSession
    ) -> Session:
        """Fetch a session, requiring it belongs to `campaign_id`, or raise 404."""
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None or session.campaign_id != campaign_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        return session

    async def _require_membership(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the requester's membership in `campaign_id`, or raise 403."""
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this campaign",
            )
        return member

    async def _require_dm(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the requester's membership, requiring the DM role, or raise 403."""
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can do this",
            )
        return member
