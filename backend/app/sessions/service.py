"""SessionService orchestrates game session and session note management."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.sessions.domain import OnlyDmCanWritePrivateNoteError, validate_note_author
from app.sessions.models import Session, SessionNote
from app.sessions.schemas import SessionCreate, SessionNoteCreate, SessionRead


class SessionService:
    """Orchestrates session creation/listing and note authoring/visibility."""

    async def create_session(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: SessionCreate,
        db: AsyncSession,
    ) -> Session:
        """Create a session with the next sequential number; DM-only."""
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can create sessions",
            )

        max_number = await db.execute(
            select(func.max(Session.session_number)).where(
                Session.campaign_id == campaign_id
            )
        )
        next_number = (max_number.scalar_one_or_none() or 0) + 1

        session = Session(
            campaign_id=campaign_id,
            session_number=next_number,
            title=data.title,
            scheduled_date=data.scheduled_date,
            summary=data.summary,
            dm_notes=data.dm_notes,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def list_sessions(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[SessionRead]:
        """List a campaign's sessions, in order; requester must be a member.

        Builds the read schema directly (rather than mutating the ORM rows)
        so hiding `dm_notes` from non-DM viewers never risks persisting a
        cleared value back to the database.
        """
        member = await self._require_membership(campaign_id, requester_id, db)
        result = await db.execute(
            select(Session)
            .where(Session.campaign_id == campaign_id)
            .order_by(Session.session_number)
        )
        is_dm = member.role == CampaignRole.dm
        return [
            SessionRead(
                id=s.id,
                campaign_id=s.campaign_id,
                session_number=s.session_number,
                title=s.title,
                scheduled_date=s.scheduled_date,
                status=s.status,
                dm_notes=s.dm_notes if is_dm else None,
                summary=s.summary,
                created_at=s.created_at,
            )
            for s in result.scalars().all()
        ]

    async def add_note(
        self,
        session_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: SessionNoteCreate,
        db: AsyncSession,
    ) -> SessionNote:
        """Add a note to a session; only the DM may mark a note private."""
        session, member = await self._require_session_membership(
            session_id, requester_id, db
        )
        try:
            validate_note_author(
                is_private=data.is_private,
                author_is_dm=member.role == CampaignRole.dm,
            )
        except OnlyDmCanWritePrivateNoteError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
            ) from exc

        note = SessionNote(
            session_id=session.id,
            author_id=requester_id,
            content=data.content,
            is_private=data.is_private,
        )
        db.add(note)
        await db.commit()
        await db.refresh(note)
        return note

    async def list_notes(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[SessionNote]:
        """List a session's notes; the DM sees all, everyone else sees public ones."""
        session, member = await self._require_session_membership(
            session_id, requester_id, db
        )
        stmt = select(SessionNote).where(SessionNote.session_id == session.id)
        if member.role != CampaignRole.dm:
            stmt = stmt.where(SessionNote.is_private.is_(False))
        result = await db.execute(stmt.order_by(SessionNote.created_at))
        return list(result.scalars().all())

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

    async def _require_session_membership(
        self, session_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> tuple[Session, CampaignMember]:
        """Fetch a session and the requester's membership in its campaign."""
        result = await db.execute(select(Session).where(Session.id == session_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Session not found"
            )
        member = await self._require_membership(session.campaign_id, requester_id, db)
        return session, member
