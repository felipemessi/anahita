"""Cross-domain queries spanning User → CampaignMember → Campaign."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.models import Campaign, CampaignMember


async def list_campaigns_for_user(
    user_id: uuid.UUID, db: AsyncSession
) -> list[Campaign]:
    """Return every campaign `user_id` is a member of, as DM or player."""
    result = await db.execute(
        select(Campaign)
        .join(CampaignMember, CampaignMember.campaign_id == Campaign.id)
        .where(CampaignMember.user_id == user_id)
        .order_by(Campaign.created_at)
    )
    return list(result.scalars().all())


async def get_membership_for_user(
    campaign_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession
) -> CampaignMember | None:
    """Return `user_id`'s membership row in `campaign_id`, or None if not a member.

    Cross-domain helper reused outside the campaigns domain (e.g. catalog's
    homebrew-creation DM check) to avoid depending on `CampaignService`.
    """
    result = await db.execute(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def list_members_for_campaign(
    campaign_id: uuid.UUID, db: AsyncSession
) -> list[CampaignMember]:
    """Return every membership row for `campaign_id`."""
    result = await db.execute(
        select(CampaignMember)
        .where(CampaignMember.campaign_id == campaign_id)
        .order_by(CampaignMember.joined_at)
    )
    return list(result.scalars().all())
