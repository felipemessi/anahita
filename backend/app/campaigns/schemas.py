"""Pydantic request/response schemas for the campaigns domain."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.campaigns.domain import CampaignRole, CampaignStatus
from app.handouts.domain import HandoutType
from app.sessions.schemas import SessionRead
from app.world.schemas import LocationRead, NPCRead


class CampaignCreate(BaseModel):
    """Request body to create a campaign."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    setting: str | None = None


class CampaignUpdate(BaseModel):
    """Request body to update a campaign's general settings.

    Every field is optional — only the ones supplied are changed (mirrors
    `characters.schemas.CharacterUpdate`).
    """

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    setting: str | None = None


class CampaignRead(BaseModel):
    """Response schema for a campaign."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    setting: str | None
    owner_id: uuid.UUID
    status: CampaignStatus
    created_at: datetime


class CampaignMemberRead(BaseModel):
    """Response schema for a campaign membership."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    user_id: uuid.UUID
    role: CampaignRole
    joined_at: datetime


class CampaignInviteCreate(BaseModel):
    """Request body to create a campaign invite."""

    role: CampaignRole = CampaignRole.player
    expires_in_hours: int = Field(default=72, gt=0, le=24 * 30)


class CampaignInviteRead(BaseModel):
    """Response schema for a campaign invite."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campaign_id: uuid.UUID
    invite_code: str
    role: CampaignRole
    expires_at: datetime
    used_by: uuid.UUID | None


class CampaignInviteRedeem(BaseModel):
    """Request body to redeem a campaign invite."""

    invite_code: str


class DashboardHandoutRead(BaseModel):
    """A pending (unrevealed) handout, as summarized on the dashboard."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    handout_type: HandoutType
    created_at: datetime


class CampaignDashboardRead(BaseModel):
    """Cross-domain dashboard summary for a campaign, shaped by the requester's role.

    `pending_handouts`/`pending_handouts_count` are always empty for a
    player — a player never sees an unrevealed handout anywhere else in the
    app (PRD §7.8), so the dashboard must not leak that one exists either.
    """

    next_session: SessionRead | None
    recent_npcs: list[NPCRead]
    recent_locations: list[LocationRead]
    pending_handouts: list[DashboardHandoutRead]
    pending_handouts_count: int
