"""Integration tests for TimelineService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.sessions.models import Session
from app.timeline.schemas import TimelineEventCreate, TimelineEventUpdate
from app.timeline.service import TimelineService


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_campaign_with_dm_and_player(
    db: AsyncSession,
) -> tuple[Campaign, User, User]:
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    campaign = Campaign(name="Test Table", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    db.add_all(
        [
            CampaignMember(
                campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm
            ),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
        ]
    )
    await db.commit()
    return campaign, dm, player


async def _make_session(
    db: AsyncSession, *, campaign_id: uuid.UUID, number: int, summary: str | None
) -> Session:
    session = Session(
        campaign_id=campaign_id,
        session_number=number,
        title=f"Session {number}",
        summary=summary,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def test_only_sessions_with_summary_produce_automatic_entries(
    db: AsyncSession,
) -> None:
    """A session without a `summary` is not turned into a timeline entry."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    await _make_session(db, campaign_id=campaign.id, number=1, summary="They arrive.")
    await _make_session(db, campaign_id=campaign.id, number=2, summary=None)
    service = TimelineService()

    timeline = await service.get_timeline(campaign.id, dm.id, db)

    assert len(timeline) == 1
    assert timeline[0].entry_type == "session"
    assert timeline[0].sort_order == 1000


async def test_manual_events_interleave_with_automatic_entries_by_sort_order(
    db: AsyncSession,
) -> None:
    """Manual events and automatic session entries merge into one ordered list."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    await _make_session(db, campaign_id=campaign.id, number=1, summary="Session one.")
    await _make_session(db, campaign_id=campaign.id, number=2, summary="Session two.")
    service = TimelineService()

    await service.create_event(
        campaign.id,
        dm.id,
        TimelineEventCreate(title="A prophecy foretold", sort_order=1500),
        db,
    )

    timeline = await service.get_timeline(campaign.id, dm.id, db)

    assert [e.title for e in timeline] == [
        "Session 1",
        "A prophecy foretold",
        "Session 2",
    ]
    assert [e.entry_type for e in timeline] == ["session", "event", "session"]


async def test_player_can_read_but_not_write_manual_events(db: AsyncSession) -> None:
    """A player can read the timeline but cannot create a manual event."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = TimelineService()

    timeline = await service.get_timeline(campaign.id, player.id, db)
    assert timeline == []

    with pytest.raises(HTTPException) as exc:
        await service.create_event(
            campaign.id, player.id, TimelineEventCreate(title="Fake", sort_order=1), db
        )
    assert exc.value.status_code == 403


async def test_dm_can_update_and_delete_manual_event(db: AsyncSession) -> None:
    """The DM can update and delete a manual event; a player cannot."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = TimelineService()
    event = await service.create_event(
        campaign.id, dm.id, TimelineEventCreate(title="Draft", sort_order=1), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.update_event(
            event.id, player.id, TimelineEventUpdate(title="Hacked"), db
        )
    assert exc.value.status_code == 403

    updated = await service.update_event(
        event.id, dm.id, TimelineEventUpdate(title="Final title"), db
    )
    assert updated.title == "Final title"

    with pytest.raises(HTTPException) as exc:
        await service.delete_event(event.id, player.id, db)
    assert exc.value.status_code == 403

    await service.delete_event(event.id, dm.id, db)
    timeline = await service.get_timeline(campaign.id, dm.id, db)
    assert timeline == []
