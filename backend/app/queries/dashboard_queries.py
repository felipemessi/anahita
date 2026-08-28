"""Cross-domain query: a campaign's dashboard (sessions + world + handouts)."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.handouts.models import Handout
from app.sessions.domain import SessionStatus
from app.sessions.models import Session
from app.world.models import NPC, Location

_RECENT_LIMIT = 5


@dataclass
class CampaignDashboard:
    """A campaign's dashboard summary, already shaped by the requester's role."""

    next_session: Session | None
    recent_npcs: list[NPC]
    recent_locations: list[Location]
    pending_handouts: list[Handout]
    pending_handouts_count: int


async def get_campaign_dashboard(
    campaign_id: uuid.UUID, *, is_dm: bool, db: AsyncSession
) -> CampaignDashboard:
    """Build a campaign's dashboard summary.

    `is_dm` gates pending (unrevealed) handouts: a player never sees an
    unrevealed handout anywhere else in the app, so for a player the
    dashboard must not leak that one exists either — the list and count
    come back empty regardless of what actually exists.
    """
    # The server's UTC "today" can be a calendar day behind a requester in a
    # negative UTC offset (e.g. the Americas) relative to the plain calendar
    # date they picked for `scheduled_date` (which carries no timezone of its
    # own). Backdating the cutoff by one day absorbs that skew without
    # requiring a per-user/campaign timezone (not tracked today) to do this
    # precisely — see docs/anahita-backend-backlog.md Fase 9.
    today = datetime.now(UTC).date()
    cutoff = today - timedelta(days=1)
    next_session_result = await db.execute(
        select(Session)
        .where(
            Session.campaign_id == campaign_id,
            # A session with no scheduled_date is still a legitimate "next
            # session" candidate — it must not be invisible forever just
            # because it was quick-created without a date.
            or_(
                Session.scheduled_date.is_(None),
                Session.scheduled_date >= cutoff,
            ),
            Session.status.in_([SessionStatus.planned, SessionStatus.in_progress]),
        )
        .order_by(
            Session.scheduled_date.is_(None),
            Session.scheduled_date,
            Session.session_number,
        )
        .limit(1)
    )
    next_session = next_session_result.scalar_one_or_none()

    recent_npcs_result = await db.execute(
        select(NPC)
        .where(NPC.campaign_id == campaign_id)
        .order_by(NPC.created_at.desc())
        .limit(_RECENT_LIMIT)
    )
    recent_locations_result = await db.execute(
        select(Location)
        .where(Location.campaign_id == campaign_id)
        .order_by(Location.created_at.desc())
        .limit(_RECENT_LIMIT)
    )

    pending_handouts: list[Handout] = []
    pending_count = 0
    if is_dm:
        pending_result = await db.execute(
            select(Handout)
            .where(Handout.campaign_id == campaign_id, Handout.is_revealed.is_(False))
            .order_by(Handout.created_at.desc())
        )
        pending_handouts = list(pending_result.scalars().all())
        pending_count = len(pending_handouts)

    return CampaignDashboard(
        next_session=next_session,
        recent_npcs=list(recent_npcs_result.scalars().all()),
        recent_locations=list(recent_locations_result.scalars().all()),
        pending_handouts=pending_handouts,
        pending_handouts_count=pending_count,
    )
