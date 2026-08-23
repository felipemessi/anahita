"""CampaignService orchestrates campaign creation and membership."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.campaigns.schemas import CampaignCreate


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
