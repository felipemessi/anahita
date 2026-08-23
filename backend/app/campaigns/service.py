"""CampaignService orchestrates campaign creation, membership, and invites."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignInvite, CampaignMember
from app.campaigns.schemas import CampaignCreate, CampaignInviteCreate
from app.queries.campaign_queries import list_members_for_campaign


class CampaignService:
    """Orchestrates campaign operations."""

    async def create_campaign(
        self, owner_id: uuid.UUID, data: CampaignCreate, db: AsyncSession
    ) -> Campaign:
        """Create a campaign and make the owner its DM automatically."""
        campaign = Campaign(
            name=data.name,
            description=data.description,
            setting=data.setting,
            owner_id=owner_id,
        )
        db.add(campaign)
        await db.flush()
        db.add(
            CampaignMember(
                campaign_id=campaign.id,
                user_id=owner_id,
                role=CampaignRole.dm,
            )
        )
        await db.commit()
        await db.refresh(campaign)
        return campaign

    async def create_invite(
        self,
        campaign_id: uuid.UUID,
        requester_id: uuid.UUID,
        data: CampaignInviteCreate,
        db: AsyncSession,
    ) -> CampaignInvite:
        """Generate a campaign invite; only the campaign's DM may do this."""
        await self._require_dm(campaign_id, requester_id, db)

        invite = CampaignInvite(
            campaign_id=campaign_id,
            invite_code=secrets.token_urlsafe(16),
            role=data.role,
            expires_at=datetime.now(UTC) + timedelta(hours=data.expires_in_hours),
        )
        db.add(invite)
        await db.commit()
        await db.refresh(invite)
        return invite

    async def redeem_invite(
        self, invite_code: str, user_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Redeem an invite code, enrolling the user with the invite's role."""
        result = await db.execute(
            select(CampaignInvite).where(CampaignInvite.invite_code == invite_code)
        )
        invite = result.scalar_one_or_none()
        if invite is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found"
            )
        if invite.used_by is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Invite already used"
            )
        # Compare naively: SQLite round-trips DateTime(timezone=True) as naive
        # UTC, so mixing it with an aware `datetime.now(UTC)` raises TypeError.
        if invite.expires_at.replace(tzinfo=None) < datetime.now(UTC).replace(
            tzinfo=None
        ):
            raise HTTPException(
                status_code=status.HTTP_410_GONE, detail="Invite has expired"
            )

        member = CampaignMember(
            campaign_id=invite.campaign_id, user_id=user_id, role=invite.role
        )
        db.add(member)
        invite.used_by = user_id
        await db.commit()
        await db.refresh(member)
        return member

    async def get_own_membership(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
    ) -> CampaignMember:
        """Return the requester's own membership in `campaign_id`.

        Lets a client discover its own `campaign_member_id` (e.g. to create a
        character) without exposing other members' rows.
        """
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not a member of this campaign",
            )
        return member

    async def get_campaign(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
    ) -> Campaign:
        """Return a campaign's detail. Viewable by any of its members."""
        await self.get_own_membership(campaign_id, user_id, db)
        result = await db.execute(
            select(Campaign).where(Campaign.id == campaign_id)
        )
        campaign = result.scalar_one_or_none()
        if campaign is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found"
            )
        return campaign

    async def list_members(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
    ) -> list[CampaignMember]:
        """List every member of `campaign_id`. Viewable by any of its members."""
        await self.get_own_membership(campaign_id, user_id, db)
        return await list_members_for_campaign(campaign_id, db)

    async def _require_dm(
        self, campaign_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
    ) -> None:
        """Raise 403 unless `user_id` is the DM of `campaign_id`."""
        result = await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None or member.role != CampaignRole.dm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the campaign's DM can perform this action",
            )
