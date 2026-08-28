"""Tests for the cross-domain campaign dashboard query."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.handouts.domain import HandoutType
from app.handouts.models import Handout
from app.queries.dashboard_queries import get_campaign_dashboard
from app.sessions.domain import SessionStatus
from app.sessions.models import Session
from app.world.domain import LocationType
from app.world.models import NPC, Location

_TODAY = datetime.now(UTC).date()


async def _make_campaign(db: AsyncSession) -> Campaign:
    owner = User(email="dm@example.com", username="dm", hashed_password="x")
    db.add(owner)
    await db.flush()
    campaign = Campaign(name="Test Campaign", owner_id=owner.id)
    db.add(campaign)
    await db.flush()
    db.add(
        CampaignMember(campaign_id=campaign.id, user_id=owner.id, role=CampaignRole.dm)
    )
    await db.flush()
    return campaign


async def test_next_session_returns_nearest_future_planned_session(
    db: AsyncSession,
) -> None:
    """The nearest future planned/in_progress session wins, not the nearest past one."""
    campaign = await _make_campaign(db)
    db.add_all(
        [
            Session(
                campaign_id=campaign.id,
                session_number=1,
                title="Past session",
                scheduled_date=_TODAY - timedelta(days=7),
                status=SessionStatus.completed,
            ),
            Session(
                campaign_id=campaign.id,
                session_number=2,
                title="Far future",
                scheduled_date=_TODAY + timedelta(days=14),
                status=SessionStatus.planned,
            ),
            Session(
                campaign_id=campaign.id,
                session_number=3,
                title="Nearest future",
                scheduled_date=_TODAY + timedelta(days=3),
                status=SessionStatus.planned,
            ),
        ]
    )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is not None
    assert dashboard.next_session.title == "Nearest future"


async def test_next_session_ignores_completed_sessions_in_the_future(
    db: AsyncSession,
) -> None:
    """A completed session scheduled in the future is never "next"."""
    campaign = await _make_campaign(db)
    db.add(
        Session(
            campaign_id=campaign.id,
            session_number=1,
            title="Already wrapped",
            scheduled_date=_TODAY + timedelta(days=1),
            status=SessionStatus.completed,
        )
    )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is None


async def test_next_session_falls_back_to_undated_planned_session(
    db: AsyncSession,
) -> None:
    """A quick-created session with no scheduled_date must not stay invisible forever."""
    campaign = await _make_campaign(db)
    db.add(
        Session(
            campaign_id=campaign.id,
            session_number=1,
            title="Quick-created, no date yet",
            scheduled_date=None,
            status=SessionStatus.planned,
        )
    )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is not None
    assert dashboard.next_session.title == "Quick-created, no date yet"


async def test_next_session_prefers_dated_session_over_undated(
    db: AsyncSession,
) -> None:
    """A dated, upcoming session still wins over an undated one."""
    campaign = await _make_campaign(db)
    db.add_all(
        [
            Session(
                campaign_id=campaign.id,
                session_number=1,
                title="No date yet",
                scheduled_date=None,
                status=SessionStatus.planned,
            ),
            Session(
                campaign_id=campaign.id,
                session_number=2,
                title="Scheduled",
                scheduled_date=_TODAY + timedelta(days=2),
                status=SessionStatus.planned,
            ),
        ]
    )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is not None
    assert dashboard.next_session.title == "Scheduled"


async def test_next_session_scheduled_for_today_appears_regardless_of_server_timezone(
    db: AsyncSession,
) -> None:
    """A session scheduled for "today" must show up even if the server's UTC
    calendar day has already rolled past the requester's local "today" (a
    requester in a negative UTC offset, e.g. the Americas)."""
    campaign = await _make_campaign(db)
    db.add(
        Session(
            campaign_id=campaign.id,
            session_number=1,
            title="Tonight's session",
            scheduled_date=_TODAY - timedelta(days=1),
            status=SessionStatus.planned,
        )
    )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is not None
    assert dashboard.next_session.title == "Tonight's session"


async def test_pending_handouts_only_returned_for_dm(db: AsyncSession) -> None:
    """A player never sees pending (unrevealed) handouts, not even a count."""
    campaign = await _make_campaign(db)
    db.add_all(
        [
            Handout(
                campaign_id=campaign.id,
                title="Secret map",
                handout_type=HandoutType.map,
                is_revealed=False,
            ),
            Handout(
                campaign_id=campaign.id,
                title="Already shown",
                handout_type=HandoutType.text,
                is_revealed=True,
            ),
        ]
    )
    await db.flush()

    dm_dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)
    player_dashboard = await get_campaign_dashboard(campaign.id, is_dm=False, db=db)

    assert dm_dashboard.pending_handouts_count == 1
    assert [h.title for h in dm_dashboard.pending_handouts] == ["Secret map"]
    assert player_dashboard.pending_handouts_count == 0
    assert player_dashboard.pending_handouts == []


async def test_recent_npcs_and_locations_respect_limit_and_order(
    db: AsyncSession,
) -> None:
    """Recent NPCs/locations come back newest-first, capped at the limit."""
    campaign = await _make_campaign(db)
    for i in range(7):
        db.add(
            NPC(
                campaign_id=campaign.id,
                name=f"NPC {i}",
                race="human",
                description="",
            )
        )
        db.add(
            Location(
                campaign_id=campaign.id,
                name=f"Location {i}",
                location_type=LocationType.town,
                description="",
            )
        )
    await db.flush()

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert len(dashboard.recent_npcs) == 5
    assert len(dashboard.recent_locations) == 5
    assert dashboard.recent_npcs[0].name == "NPC 6"
    assert dashboard.recent_locations[0].name == "Location 6"


async def test_dashboard_empty_campaign_returns_empty_shape(db: AsyncSession) -> None:
    """A campaign with nothing in it returns an empty shape, not an error."""
    campaign = await _make_campaign(db)

    dashboard = await get_campaign_dashboard(campaign.id, is_dm=True, db=db)

    assert dashboard.next_session is None
    assert dashboard.recent_npcs == []
    assert dashboard.recent_locations == []
    assert dashboard.pending_handouts == []
    assert dashboard.pending_handouts_count == 0
