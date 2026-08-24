"""JournalService orchestrates the DM's private campaign journal."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.journal.models import JournalEntry
from app.journal.schemas import JournalEntryCreate, JournalEntryUpdate
from app.sessions.models import Session


class JournalService:
    """Orchestrates journal entry CRUD. Every operation is DM-only."""

    async def create_entry(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: JournalEntryCreate,
        db: AsyncSession,
    ) -> JournalEntry:
        """Create a journal entry; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)
        if data.session_id is not None:
            await self._require_same_campaign_session(data.session_id, campaign_id, db)

        entry = JournalEntry(
            campaign_id=campaign_id,
            author_id=requester_id,
            title=data.title,
            content=data.content,
            session_id=data.session_id,
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    async def list_entries(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[JournalEntry]:
        """List a campaign's journal entries, most recent first. DM-only."""
        await self._require_dm(campaign_id, requester_id, db)
        result = await db.execute(
            select(JournalEntry)
            .where(JournalEntry.campaign_id == campaign_id)
            .order_by(JournalEntry.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_entry(
        self,
        entry_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: JournalEntryUpdate,
        db: AsyncSession,
    ) -> JournalEntry:
        """Update a journal entry's title/content/session link. DM-only."""
        entry = await self._require_entry(entry_id, db)
        await self._require_dm(entry.campaign_id, requester_id, db)

        if data.title is not None:
            entry.title = data.title
        if data.content is not None:
            entry.content = data.content
        if data.session_id is not None:
            await self._require_same_campaign_session(
                data.session_id, entry.campaign_id, db
            )
            entry.session_id = data.session_id
        await db.commit()
        await db.refresh(entry)
        return entry

    async def delete_entry(
        self, entry_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Delete a journal entry. DM-only."""
        entry = await self._require_entry(entry_id, db)
        await self._require_dm(entry.campaign_id, requester_id, db)
        await db.delete(entry)
        await db.commit()

    async def _require_entry(
        self, entry_id: uuid.UUID, db: AsyncSession
    ) -> JournalEntry:
        """Fetch a journal entry by id, or raise 404."""
        result = await db.execute(
            select(JournalEntry).where(JournalEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found"
            )
        return entry

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

    async def _require_dm(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Fetch the requester's membership, requiring the DM role, or raise 403.

        Journal entries are never visible to players, so any non-member or
        non-DM request is rejected with the same 403 — no distinction is
        made between "not a member" and "member but not DM" here, since a
        player must never learn whether an entry exists either way.
        """
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == requester_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None or member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can do this",
            )
        return member
