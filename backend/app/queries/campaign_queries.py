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
