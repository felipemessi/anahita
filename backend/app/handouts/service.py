"""HandoutService orchestrates handout upload, listing, and reveal.

Reveal (PRD §10.3) broadcasts a `handout_revealed` event over the combat
WebSocket to whichever encounter is currently `active` for the handout's
session — `app.combat.ws_manager.manager` is the same process-wide registry
`app.combat.ws_router` uses, so this doesn't need its own connection state.
Outside an active session, players simply see the reveal via REST on their
next `GET /campaigns/{id}/handouts`.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import CampaignMember
from app.combat.domain import EncounterStatus
from app.combat.models import Encounter
from app.combat.ws_manager import manager as combat_ws_manager
from app.handouts.models import Handout
from app.handouts.schemas import HandoutCreate, HandoutRead, HandoutRevealedEvent
from app.sessions.models import Session
from app.storage.base import StorageService


class HandoutService:
    """Orchestrates handout creation, listing, and DM-triggered reveal."""

    def __init__(self, storage: StorageService) -> None:
        """Store the StorageService used to resolve/persist handout files."""
        self._storage = storage

    async def create_handout(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: HandoutCreate,
        db: AsyncSession,
        *,
        file_bytes: bytes | None,
        file_name: str | None,
        content_type: str | None,
    ) -> HandoutRead:
        """Create a handout; only the campaign's DM may do this.

        If `data.session_id` is given, it must belong to `campaign_id`.
        """
        await self._require_dm(campaign_id, requester_id, db)
        if data.session_id is not None:
            await self._require_session_in_campaign(campaign_id, data.session_id, db)

        storage_key: str | None = None
        if file_bytes is not None:
            key = f"handouts/{campaign_id}/{uuid.uuid4()}_{file_name or 'file'}"
            storage_key = self._storage.upload(
                key, file_bytes, content_type or "application/octet-stream"
            )

        handout = Handout(
            campaign_id=campaign_id,
            session_id=data.session_id,
            title=data.title,
            content=data.content,
            handout_type=data.handout_type,
            storage_key=storage_key,
        )
        db.add(handout)
        await db.commit()
        await db.refresh(handout)
        return self._to_read(handout)

    async def list_handouts(
        self, campaign_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> list[HandoutRead]:
        """List a campaign's handouts. Non-DM members only see revealed ones."""
        member = await self._require_membership(campaign_id, requester_id, db)

        query = select(Handout).where(Handout.campaign_id == campaign_id)
        if member.role != CampaignRole.dm:
            query = query.where(Handout.is_revealed.is_(True))
        result = await db.execute(query.order_by(Handout.created_at))
        return [self._to_read(h) for h in result.scalars().all()]

    async def get_handout(
        self, handout_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> HandoutRead:
        """Get a single handout; non-DM members can only see it if revealed."""
        handout = await self._load_or_404(handout_id, db)
        member = await self._require_membership(handout.campaign_id, requester_id, db)
        if member.role != CampaignRole.dm and not handout.is_revealed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Handout not found"
            )
        return self._to_read(handout)

    async def reveal_handout(
        self, handout_id: uuid.UUID, requester_id: uuid.UUID, db: AsyncSession
    ) -> HandoutRead:
        """Reveal a handout, broadcasting to any active encounter of its session."""
        handout = await self._load_or_404(handout_id, db)
        await self._require_dm(handout.campaign_id, requester_id, db)

        handout.is_revealed = True
        handout.revealed_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(handout)

        read = self._to_read(handout)
        if handout.session_id is not None:
            await self._broadcast_reveal(handout.session_id, read, db)
        return read

    async def _broadcast_reveal(
        self, session_id: uuid.UUID, handout: HandoutRead, db: AsyncSession
    ) -> None:
        """Send `handout_revealed` to every active encounter's connected sockets."""
        result = await db.execute(
            select(Encounter).where(
                Encounter.session_id == session_id,
                Encounter.status == EncounterStatus.active,
            )
        )
        event = HandoutRevealedEvent(
            id=handout.id,
            title=handout.title,
            handout_type=handout.handout_type,
            url=handout.url,
        )
        envelope: dict[str, Any] = {
            "event_type": "handout_revealed",
            "payload": event.model_dump(mode="json"),
        }
        for encounter in result.scalars().all():
            await combat_ws_manager.broadcast(encounter.id, envelope)

    def _to_read(self, handout: Handout) -> HandoutRead:
        url = (
            self._storage.get_url(handout.storage_key) if handout.storage_key else None
        )
        return HandoutRead(
            id=handout.id,
            campaign_id=handout.campaign_id,
            session_id=handout.session_id,
            title=handout.title,
            content=handout.content,
            handout_type=handout.handout_type,
            url=url,
            is_revealed=handout.is_revealed,
            revealed_at=handout.revealed_at,
            created_at=handout.created_at,
        )

    async def _load_or_404(self, handout_id: uuid.UUID, db: AsyncSession) -> Handout:
        result = await db.execute(select(Handout).where(Handout.id == handout_id))
        handout = result.scalar_one_or_none()
        if handout is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Handout not found"
            )
        return handout

    async def _require_session_in_campaign(
        self, campaign_id: uuid.UUID, session_id: uuid.UUID, db: AsyncSession
    ) -> Session:
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
        member = await self._require_membership(campaign_id, requester_id, db)
        if member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can manage handouts",
            )
        return member
