"""Tests for CharacterService.get_character_sessions: auth + DM-notes visibility."""

import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.combat.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.characters.models import Character
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


async def _make_fixture(db: AsyncSession) -> tuple[User, User, User, uuid.UUID]:
    """DM + owning player + an outsider, one campaign, one character for the player."""
    dm = await _make_user(db, email="dm@example.com")
    player = await _make_user(db, email="player@example.com")
    outsider = await _make_user(db, email="outsider@example.com")

    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()

    db.add_all(
        [
            CampaignMember(campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
        ]
    )
    await db.flush()

    member_result = await db.execute(
        select(CampaignMember).where(
            CampaignMember.campaign_id == campaign.id,
            CampaignMember.user_id == player.id,
        )
    )
    player_member = member_result.scalar_one()

    character = Character(
        campaign_member_id=player_member.id,
        name="Aldric",
        race_id=uuid.uuid4(),
        level=1,
        hit_point_max=10,
        hit_point_current=10,
        armor_class=14,
        speed=30,
        proficiency_bonus=2,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)

    session = Session(
        campaign_id=campaign.id,
        session_number=1,
        title="Session 1",
        status=SessionStatus.completed,
        dm_notes="Secret DM plans",
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.flush()

    encounter = Encounter(
        session_id=session.id, name="Ambush", status=EncounterStatus.preparing
    )
    db.add(encounter)
    await db.flush()
    db.add(
        EncounterParticipant(
            encounter_id=encounter.id,
            character_id=character.id,
            name="Aldric",
            hit_point_max=10,
            hit_point_current=10,
            armor_class=14,
            turn_order=0,
        )
    )
    await db.commit()

    return dm, player, outsider, character.id


async def test_get_character_sessions_empty_for_new_character(db: AsyncSession) -> None:
    """A character never in an encounter has an empty session list."""
    dm = await _make_user(db, email="dm@example.com")
    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    member = CampaignMember(campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm)
    db.add(member)
    await db.flush()
    character = Character(
        campaign_member_id=member.id,
        name="Solo",
        race_id=uuid.uuid4(),
        level=1,
        hit_point_max=10,
        hit_point_current=10,
        armor_class=14,
        speed=30,
        proficiency_bonus=2,
    )
    db.add(character)
    await db.commit()
    await db.refresh(character)

    service = CharacterService()
    sessions = await service.get_character_sessions(character.id, dm.id, db)
    assert sessions == []


async def test_get_character_sessions_reflects_participation_for_owner(
    db: AsyncSession,
) -> None:
    """The owning player sees the sessions their character actually fought in."""
    _dm, player, _outsider, character_id = await _make_fixture(db)
    service = CharacterService()

    sessions = await service.get_character_sessions(character_id, player.id, db)

    assert len(sessions) == 1
    assert sessions[0].session_number == 1
    assert sessions[0].dm_notes is None


async def test_get_character_sessions_shows_dm_notes_to_dm(db: AsyncSession) -> None:
    """The campaign DM sees `dm_notes`; the owning player does not."""
    dm, _player, _outsider, character_id = await _make_fixture(db)
    service = CharacterService()

    sessions = await service.get_character_sessions(character_id, dm.id, db)

    assert sessions[0].dm_notes == "Secret DM plans"


async def test_get_character_sessions_forbidden_for_outsider(db: AsyncSession) -> None:
    """A user who's neither the owner nor the DM cannot view the sessions list."""
    _dm, _player, outsider, character_id = await _make_fixture(db)
    service = CharacterService()

    with pytest.raises(HTTPException) as exc_info:
        await service.get_character_sessions(character_id, outsider.id, db)
    assert exc_info.value.status_code == 403
