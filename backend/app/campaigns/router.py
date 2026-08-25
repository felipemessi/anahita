"""HTTP router for the campaigns domain."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.schemas import (
    CampaignCreate,
    CampaignDashboardRead,
    CampaignInviteCreate,
    CampaignInviteRead,
    CampaignInviteRedeem,
    CampaignMemberRead,
    CampaignRead,
    CampaignUpdate,
    DashboardHandoutRead,
)
from app.campaigns.service import CampaignService
from app.core.dependencies import get_current_user
from app.database import get_db
from app.queries.campaign_queries import list_campaigns_for_user
from app.queries.dashboard_queries import get_campaign_dashboard
from app.sessions.schemas import SessionRead
from app.world.schemas import LocationRead, NPCRead

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


@router.get("/{campaign_id}", response_model=CampaignRead)
async def get_campaign(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignRead:
    """Get a campaign's detail. Viewable by any of its members."""
    campaign = await service.get_campaign(campaign_id, user.id, db)
    return CampaignRead.model_validate(campaign)


@router.patch("/{campaign_id}", response_model=CampaignRead)
async def update_campaign(
    campaign_id: uuid.UUID,
    body: CampaignUpdate,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignRead:
    """Update a campaign's general settings. Only the campaign's DM may do this."""
    campaign = await service.update_campaign(campaign_id, user.id, body, db)
    return CampaignRead.model_validate(campaign)


@router.get("/{campaign_id}/members", response_model=list[CampaignMemberRead])
async def list_members(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> list[CampaignMemberRead]:
    """List every member of a campaign. Viewable by any of its members."""
    members = await service.list_members(campaign_id, user.id, db)
    return [CampaignMemberRead.model_validate(m) for m in members]


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


@router.get("/{campaign_id}/dashboard", response_model=CampaignDashboardRead)
async def get_dashboard(
    campaign_id: uuid.UUID,
    user: CurrentUser,
    db: DB,
    service: Annotated[CampaignService, Depends(get_campaign_service)],
) -> CampaignDashboardRead:
    """Get a campaign's dashboard summary. Viewable by any of its members.

    A player's `dm_notes` on `next_session` and pending-handouts fields come
    back hidden/empty, same as the rest of the app (`GET .../sessions`,
    handouts never listed unrevealed to a player).
    """
    member = await service.get_own_membership(campaign_id, user.id, db)
    is_dm = member.role == CampaignRole.dm
    dashboard = await get_campaign_dashboard(campaign_id, is_dm=is_dm, db=db)
    next_session = (
        SessionRead(
            id=dashboard.next_session.id,
            campaign_id=dashboard.next_session.campaign_id,
            session_number=dashboard.next_session.session_number,
            title=dashboard.next_session.title,
            scheduled_date=dashboard.next_session.scheduled_date,
            status=dashboard.next_session.status,
            dm_notes=dashboard.next_session.dm_notes if is_dm else None,
            summary=dashboard.next_session.summary,
            created_at=dashboard.next_session.created_at,
        )
        if dashboard.next_session is not None
        else None
    )
    return CampaignDashboardRead(
        next_session=next_session,
        recent_npcs=[NPCRead.model_validate(n) for n in dashboard.recent_npcs],
        recent_locations=[
            LocationRead.model_validate(loc) for loc in dashboard.recent_locations
        ],
        pending_handouts=[
            DashboardHandoutRead.model_validate(h) for h in dashboard.pending_handouts
        ],
        pending_handouts_count=dashboard.pending_handouts_count,
    )


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
