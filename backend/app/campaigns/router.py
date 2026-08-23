"""HTTP router for the campaigns domain."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.schemas import CampaignCreate, CampaignRead
from app.campaigns.service import CampaignService
from app.core.dependencies import get_current_user
from app.database import get_db

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_campaign_service() -> CampaignService:
    """Return a CampaignService instance."""
    return CampaignService()


@router.post("", response_model=CampaignRead, status_code=status.HTTP_201_CREATED)
async def create_campaign(
    body: CampaignCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignRead:
    """Create a campaign; the authenticated user becomes its DM."""
    campaign = await service.create_campaign(user.id, body, db)
    return CampaignRead.model_validate(campaign)
