"""Tests for the cross-domain character-sessions query."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.characters.models import Character
from app.combat.domain import EncounterStatus
from app.combat.models import Encounter, EncounterParticipant
from app.queries.character_sessions import get_sessions_for_character
from app.sessions.domain import SessionStatus
from app.sessions.models import Session


async def _make_campaign_with_character(db: AsyncSession) -> tuple[uuid.UUID, uuid.UUID]:
    """Create a campaign, a player character, and return (campaign_id, character_id)."""
    suffix = uuid.uuid4().hex[:8]
    dm = User(email=f"dm-{suffix}@example.com", username=f"dm-{suffix}", hashed_password="x")
    player = User(
        email=f"player-{suffix}@example.com",
        username=f"player-{suffix}",
        hashed_password="x",
    )
    db.add_all([dm, player])
    await db.flush()

    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()

    player_member = CampaignMember(
        campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
    )
    db.add(player_member)
    await db.flush()

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
    return campaign.id, character.id


async def _make_session(
    db: AsyncSession, campaign_id: uuid.UUID, *, session_number: int
) -> Session:
    session = Session(
        campaign_id=campaign_id,
        session_number=session_number,
        title=f"Session {session_number}",
        status=SessionStatus.completed,
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def _add_participant(
    db: AsyncSession, session_id: uuid.UUID, character_id: uuid.UUID
) -> None:
    encounter = Encounter(
        session_id=session_id, name="Ambush", status=EncounterStatus.preparing
    )
    db.add(encounter)
    await db.flush()
    db.add(
        EncounterParticipant(
            encounter_id=encounter.id,
            character_id=character_id,
            name="Aldric",
            hit_point_max=10,
            hit_point_current=10,
            armor_class=14,
            turn_order=0,
        )
    )
    await db.commit()


async def test_get_sessions_for_character_empty_when_no_participation(
    db: AsyncSession,
) -> None:
    """A character never added to an encounter has no associated sessions."""
    _, character_id = await _make_campaign_with_character(db)
    assert await get_sessions_for_character(character_id, db) == []


async def test_get_sessions_for_character_reflects_combat_participation(
    db: AsyncSession,
) -> None:
    """A character appears for every session it fought in, ordered by number."""
    campaign_id, character_id = await _make_campaign_with_character(db)
    session_2 = await _make_session(db, campaign_id, session_number=2)
    session_1 = await _make_session(db, campaign_id, session_number=1)
    await _add_participant(db, session_2.id, character_id)
    await _add_participant(db, session_1.id, character_id)

    sessions = await get_sessions_for_character(character_id, db)

    assert [s.session_number for s in sessions] == [1, 2]


async def test_get_sessions_for_character_ignores_other_characters(
    db: AsyncSession,
) -> None:
    """Another character's combat participation never leaks into this one's list."""
    campaign_id, character_id = await _make_campaign_with_character(db)
    _, other_character_id = await _make_campaign_with_character(db)
    session = await _make_session(db, campaign_id, session_number=1)
    await _add_participant(db, session.id, other_character_id)

    assert await get_sessions_for_character(character_id, db) == []


async def test_get_sessions_for_character_deduplicates_multiple_encounters(
    db: AsyncSession,
) -> None:
    """Fighting in two encounters within the same session counts it once."""
    campaign_id, character_id = await _make_campaign_with_character(db)
    session = await _make_session(db, campaign_id, session_number=1)
    await _add_participant(db, session.id, character_id)
    await _add_participant(db, session.id, character_id)

    sessions = await get_sessions_for_character(character_id, db)

    assert len(sessions) == 1
