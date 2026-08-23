"""HTTP router for the campaigns domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.schemas import (
    CampaignCreate,
    CampaignInviteCreate,
    CampaignInviteRead,
    CampaignInviteRedeem,
    CampaignMemberRead,
    CampaignRead,
)
from app.campaigns.service import CampaignService
from app.core.dependencies import get_current_user
from app.database import get_db
from app.queries.campaign_queries import list_campaigns_for_user

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_campaign_service() -> CampaignService:
    """Return a CampaignService instance."""
    return CampaignService()


@router.get("", response_model=list[CampaignRead])
async def list_my_campaigns(user: CurrentUser, db: DB) -> list[CampaignRead]:
    """List every campaign the authenticated user belongs to, as DM or player."""
    campaigns = await list_campaigns_for_user(user.id, db)
    return [CampaignRead.model_validate(c) for c in campaigns]


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


@router.post(
    "/{campaign_id}/invites",
    response_model=CampaignInviteRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_invite(
    campaign_id: uuid.UUID,
    body: CampaignInviteCreate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignInviteRead:
    """Generate an invite for a campaign; only the campaign's DM may do this."""
    invite = await service.create_invite(campaign_id, user.id, body, db)
    return CampaignInviteRead.model_validate(invite)


@router.get("/{campaign_id}/members/me", response_model=CampaignMemberRead)
async def get_my_membership(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignMemberRead:
    """Return the authenticated user's own membership in a campaign."""
    member = await service.get_own_membership(campaign_id, user.id, db)
    return CampaignMemberRead.model_validate(member)


@router.post("/invites/redeem", response_model=CampaignMemberRead)
async def redeem_invite(
    body: CampaignInviteRedeem,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignMemberRead:
    """Redeem an invite code, joining the campaign with the invite's role."""
    member = await service.redeem_invite(body.invite_code, user.id, db)
    return CampaignMemberRead.model_validate(member)
