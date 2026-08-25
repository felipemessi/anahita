"""Integration tests for SessionService using SQLite in-memory database."""

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.sessions.schemas import SessionCreate, SessionNoteCreate
from app.sessions.service import SessionService


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


async def test_dm_can_create_session_with_sequential_number(
    db: AsyncSession,
) -> None:
    """Sessions are numbered sequentially per campaign, starting at 1."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()

    first = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="The Beginning"), db
    )
    second = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="The Return"), db
    )

    assert first.session_number == 1
    assert second.session_number == 2


async def test_player_cannot_create_session(db: AsyncSession) -> None:
    """A non-DM member cannot create a session."""
    campaign, _dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()

    with pytest.raises(HTTPException) as exc:
        await service.create_session(
            campaign.id, player.id, SessionCreate(title="Coup"), db
        )
    assert exc.value.status_code == 403


async def test_player_cannot_see_dm_notes(db: AsyncSession) -> None:
    """Listing sessions hides `dm_notes` from non-DM members."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    await service.create_session(
        campaign.id,
        dm.id,
        SessionCreate(title="Secret Session", dm_notes="the BBEG is the mayor"),
        db,
    )

    dm_view = await service.list_sessions(campaign.id, dm.id, db)
    player_view = await service.list_sessions(campaign.id, player.id, db)

    assert dm_view[0].dm_notes == "the BBEG is the mayor"
    assert player_view[0].dm_notes is None


async def test_player_can_see_summary_for_recap(db: AsyncSession) -> None:
    """Listing sessions exposes `summary` to every member, not just the DM.

    The Fase 5 "recap" screen (PRD §7.10) has no endpoint of its own — it
    reads `GET /campaigns/{id}/sessions` and renders each session's
    `summary` in order. This is the gap this story checks isn't there.
    """
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    await service.create_session(
        campaign.id,
        dm.id,
        SessionCreate(title="Session 1", summary="The party met at the inn."),
        db,
    )

    player_view = await service.list_sessions(campaign.id, player.id, db)

    assert player_view[0].summary == "The party met at the inn."


async def test_player_can_add_public_note(db: AsyncSession) -> None:
    """A player can add a public (non-private) session note."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="Session 1"), db
    )

    note = await service.add_note(
        session.id, player.id, SessionNoteCreate(content="Great fight!"), db
    )
    assert note.author_id == player.id
    assert not note.is_private


async def test_player_cannot_write_private_note(db: AsyncSession) -> None:
    """A player attempting to write a private note is rejected."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="Session 1"), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.add_note(
            session.id,
            player.id,
            SessionNoteCreate(content="secret plan", is_private=True),
            db,
        )
    assert exc.value.status_code == 403


async def test_player_does_not_see_private_notes_dm_sees_everything(
    db: AsyncSession,
) -> None:
    """The DM's private notes are hidden from players; the DM sees all notes."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="Session 1"), db
    )
    await service.add_note(
        session.id,
        dm.id,
        SessionNoteCreate(content="secret plot twist", is_private=True),
        db,
    )
    await service.add_note(
        session.id, player.id, SessionNoteCreate(content="party found a map"), db
    )

    player_notes = await service.list_notes(session.id, player.id, db)
    dm_notes = await service.list_notes(session.id, dm.id, db)

    assert [n.content for n in player_notes] == ["party found a map"]
    assert {n.content for n in dm_notes} == {"secret plot twist", "party found a map"}


async def test_non_member_cannot_access_sessions(db: AsyncSession) -> None:
    """A user with no membership in the campaign is rejected."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    outsider = await _make_user(db, email="outsider@example.com")
    service = SessionService()
    await service.create_session(campaign.id, dm.id, SessionCreate(title="S1"), db)

    with pytest.raises(HTTPException) as exc:
        await service.list_sessions(campaign.id, outsider.id, db)
    assert exc.value.status_code == 403


async def test_dm_can_open_planned_session(db: AsyncSession) -> None:
    """The DM can open a planned session for play."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="The Beginning"), db
    )

    opened = await service.open_session(session.id, dm.id, db)
    assert opened.status == "in_progress"


async def test_player_cannot_open_session(db: AsyncSession) -> None:
    """A non-DM member cannot open a session."""
    campaign, dm, player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="The Beginning"), db
    )

    with pytest.raises(HTTPException) as exc:
        await service.open_session(session.id, player.id, db)
    assert exc.value.status_code == 403


async def test_open_session_twice_conflicts(db: AsyncSession) -> None:
    """Opening an already-opened session is rejected."""
    campaign, dm, _player = await _make_campaign_with_dm_and_player(db)
    service = SessionService()
    session = await service.create_session(
        campaign.id, dm.id, SessionCreate(title="The Beginning"), db
    )
    await service.open_session(session.id, dm.id, db)

    with pytest.raises(HTTPException) as exc:
        await service.open_session(session.id, dm.id, db)
    assert exc.value.status_code == 409
