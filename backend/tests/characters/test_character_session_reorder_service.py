"""Tests for CharacterService.reorder_sessions: personal session ordering.

Covers: reordering doesn't touch `Session.session_number`, doesn't affect
another character/player's view of the same sessions, owner-only auth, and
validation of the submitted `session_ids`.
"""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.combat.models  # noqa: F401 — registers models with Base
import app.maps.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.characters.models import Character
from app.characters.schemas import CharacterSessionOrderRequest
from app.characters.service import CharacterService
from app.combat.domain import EncounterStatus
from app.combat.models import Encounter, EncounterParticipant
from app.sessions.domain import SessionStatus
from app.sessions.models import Session


async def _make_user(db: AsyncSession, *, email: str) -> User:
    user = User(email=email, username=email.split("@")[0], hashed_password="x")
    db.add(user)
    await db.flush()
    return user


async def _make_character(
    db: AsyncSession, member: CampaignMember, *, name: str
) -> Character:
    character = Character(
        campaign_member_id=member.id,
        name=name,
        race_id=uuid.uuid4(),
        level=1,
        hit_point_max=10,
        hit_point_current=10,
        armor_class=14,
        speed=30,
        proficiency_bonus=2,
    )
    db.add(character)
    await db.flush()
    return character


async def _add_to_session(
    db: AsyncSession, character: Character, session: Session
) -> None:
    encounter = Encounter(
        session_id=session.id, name=f"Encounter {session.session_number}",
        status=EncounterStatus.preparing,
    )
    db.add(encounter)
    await db.flush()
    db.add(
        EncounterParticipant(
            encounter_id=encounter.id,
            character_id=character.id,
            name=character.name,
            hit_point_max=10,
            hit_point_current=10,
            armor_class=14,
            turn_order=0,
        )
    )
    await db.flush()


async def _make_fixture(
    db: AsyncSession,
) -> tuple[User, User, User, uuid.UUID, uuid.UUID, list[Session]]:
    """DM + owning player + a second player, one campaign, two characters,
    three sessions both characters participated in.
    """
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    other_player = await _make_user(db, email="other@example.com")

    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()

    db.add_all(
        [
            CampaignMember(campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
            CampaignMember(
                campaign_id=campaign.id,
                user_id=other_player.id,
                role=CampaignRole.player,
            ),
        ]
    )
    await db.flush()

    player_member = (
        await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign.id,
                CampaignMember.user_id == player.id,
            )
        )
    ).scalar_one()
    other_member = (
        await db.execute(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign.id,
                CampaignMember.user_id == other_player.id,
            )
        )
    ).scalar_one()

    character = await _make_character(db, player_member, name="Aldric")
    other_character = await _make_character(db, other_member, name="Brenna")

    sessions = []
    for number in (1, 2, 3):
        session = Session(
            campaign_id=campaign.id,
            session_number=number,
            title=f"Session {number}",
            status=SessionStatus.completed,
            created_at=datetime.now(UTC),
        )
        db.add(session)
        await db.flush()
        sessions.append(session)
        await _add_to_session(db, character, session)
        await _add_to_session(db, other_character, session)

    await db.commit()
    for c in (character, other_character):
        await db.refresh(c)

    return dm, player, other_player, character.id, other_character.id, sessions


async def test_reorder_sessions_changes_owner_view_order(db: AsyncSession) -> None:
    """Reordering [3, 1, 2] is reflected in the owner's subsequent read."""
    _dm, player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()
    session_1, session_2, session_3 = sessions

    result = await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(
            session_ids=[session_3.id, session_1.id, session_2.id]
        ),
        db,
    )

    assert [s.id for s in result] == [session_3.id, session_1.id, session_2.id]

    reread = await service.get_character_sessions(character_id, player.id, db)
    assert [s.id for s in reread] == [session_3.id, session_1.id, session_2.id]


async def test_reorder_sessions_does_not_change_session_number(
    db: AsyncSession,
) -> None:
    """The underlying `Session.session_number` (global/official order) is untouched."""
    _dm, player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()
    session_1, session_2, session_3 = sessions

    await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(
            session_ids=[session_3.id, session_1.id, session_2.id]
        ),
        db,
    )

    for s in (session_1, session_2, session_3):
        await db.refresh(s)
    assert session_1.session_number == 1
    assert session_2.session_number == 2
    assert session_3.session_number == 3


async def test_reorder_sessions_does_not_affect_other_character(
    db: AsyncSession,
) -> None:
    """Another character's (and player's) session order is unaffected."""
    _dm, player, other_player, character_id, other_character_id, sessions = (
        await _make_fixture(db)
    )
    service = CharacterService()
    session_1, session_2, session_3 = sessions

    await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(
            session_ids=[session_3.id, session_1.id, session_2.id]
        ),
        db,
    )

    other_view = await service.get_character_sessions(
        other_character_id, other_player.id, db
    )
    assert [s.id for s in other_view] == [session_1.id, session_2.id, session_3.id]


async def test_reorder_sessions_partial_list_appends_remainder_by_session_number(
    db: AsyncSession,
) -> None:
    """Sessions omitted from the reorder request fall back to `session_number` order,
    appended after the explicitly ordered ones."""
    _dm, player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()
    session_1, session_2, session_3 = sessions

    result = await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(session_ids=[session_3.id]),
        db,
    )

    assert [s.id for s in result] == [session_3.id, session_1.id, session_2.id]


async def test_reorder_sessions_replaces_previous_order(db: AsyncSession) -> None:
    """A second reorder call replaces the first wholesale, not merges with it."""
    _dm, player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()
    session_1, session_2, session_3 = sessions

    await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(
            session_ids=[session_3.id, session_2.id, session_1.id]
        ),
        db,
    )
    result = await service.reorder_sessions(
        character_id,
        player.id,
        CharacterSessionOrderRequest(session_ids=[session_1.id]),
        db,
    )

    assert [s.id for s in result] == [session_1.id, session_2.id, session_3.id]


async def test_reorder_sessions_rejects_unknown_session_id(db: AsyncSession) -> None:
    """A session_id the character isn't associated with is rejected (422)."""
    _dm, player, _other, character_id, _other_id, _sessions = await _make_fixture(db)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc_info:
        await service.reorder_sessions(
            character_id,
            player.id,
            CharacterSessionOrderRequest(session_ids=[uuid.uuid4()]),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_reorder_sessions_rejects_duplicate_session_id(db: AsyncSession) -> None:
    """Repeating a session_id in the same request is rejected (422)."""
    _dm, player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc_info:
        await service.reorder_sessions(
            character_id,
            player.id,
            CharacterSessionOrderRequest(
                session_ids=[sessions[0].id, sessions[0].id]
            ),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_reorder_sessions_forbidden_for_dm(db: AsyncSession) -> None:
    """This is a personal preference — even the campaign DM can't set it for a player."""
    dm, _player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc_info:
        await service.reorder_sessions(
            character_id,
            dm.id,
            CharacterSessionOrderRequest(session_ids=[sessions[0].id]),
            db,
        )
    assert exc_info.value.status_code == 403


async def test_reorder_sessions_forbidden_for_outsider(db: AsyncSession) -> None:
    """A user with no membership at all cannot reorder either."""
    _dm, _player, _other, character_id, _other_id, sessions = await _make_fixture(db)
    service = CharacterService()
    outsider = await _make_user(db, email="outsider2@example.com")
    await db.commit()

    with pytest.raises(HTTPException) as exc_info:
        await service.reorder_sessions(
            character_id,
            outsider.id,
            CharacterSessionOrderRequest(session_ids=[sessions[0].id]),
            db,
        )
    assert exc_info.value.status_code == 403
