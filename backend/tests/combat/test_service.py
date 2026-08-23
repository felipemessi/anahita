"""Integration tests for CombatService using SQLite in-memory database."""

import uuid

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.combat.schemas import (
    EncounterCreate,
    EncounterParticipantCreate,
    EncounterParticipantUpdate,
)
from app.combat.service import CombatService
from tests.combat.conftest import _CampaignFixture


async def test_create_encounter_by_dm(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """The DM can create an encounter for a session."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Goblin Ambush"), db
    )
    assert encounter.name == "Goblin Ambush"
    assert encounter.status == "preparing"
    assert encounter.participants == []


async def test_create_encounter_rejects_non_dm(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A player cannot create an encounter."""
    fx = campaign_with_session
    service = CombatService()
    with pytest.raises(HTTPException) as exc_info:
        await service.create_encounter(
            fx.session_id, fx.player_id, EncounterCreate(name="Ambush"), db
        )
    assert exc_info.value.status_code == 403


async def test_create_encounter_rejects_non_member(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """An outsider cannot create an encounter."""
    fx = campaign_with_session
    service = CombatService()
    with pytest.raises(HTTPException) as exc_info:
        await service.create_encounter(
            fx.session_id, fx.outsider_id, EncounterCreate(name="Ambush"), db
        )
    assert exc_info.value.status_code == 403


async def test_add_participant_defaults_hp_current_to_max(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Omitting hit_point_current defaults it to hit_point_max."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin",
            initiative=12,
            hit_point_max=7,
            armor_class=15,
            turn_order=0,
        ),
        db,
    )
    assert len(encounter.participants) == 1
    assert encounter.participants[0].hit_point_current == 7


async def test_add_participant_rejects_both_character_and_npc(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A participant cannot be linked to both a character and an NPC."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.add_participant(
            encounter.id,
            fx.dm_id,
            EncounterParticipantCreate(
                character_id=uuid.uuid4(),
                npc_id=uuid.uuid4(),
                name="Confused",
                initiative=10,
                hit_point_max=10,
                armor_class=10,
                turn_order=0,
            ),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_update_participant_hp_rejects_exceeding_max(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Setting hit_point_current above hit_point_max is rejected."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=12, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    with pytest.raises(HTTPException) as exc_info:
        await service.update_participant(
            encounter.id,
            participant_id,
            fx.dm_id,
            EncounterParticipantUpdate(hit_point_current=999),
            db,
        )
    assert exc_info.value.status_code == 422


async def test_update_participant_applies_damage(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A DM can reduce a participant's current HP (damage)."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=12, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    encounter = await service.update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        EncounterParticipantUpdate(hit_point_current=2),
        db,
    )
    assert encounter.participants[0].hit_point_current == 2


async def test_remove_participant(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A DM can remove a participant from the encounter."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=12, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    encounter = await service.remove_participant(
        encounter.id, participant_id, fx.dm_id, db
    )
    assert encounter.participants == []


async def test_start_encounter_transitions_to_active(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Starting a preparing encounter sets it to active with round 1."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.start_encounter(encounter.id, fx.dm_id, db)
    assert encounter.status == "active"
    assert encounter.current_round == 1


async def test_start_encounter_twice_conflicts(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Starting an already-active encounter is rejected."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    await service.start_encounter(encounter.id, fx.dm_id, db)
    with pytest.raises(HTTPException) as exc_info:
        await service.start_encounter(encounter.id, fx.dm_id, db)
    assert exc_info.value.status_code == 409


async def test_list_encounters_visible_to_player(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A player (not just the DM) can list the session's encounters."""
    fx = campaign_with_session
    service = CombatService()
    await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounters = await service.list_encounters(fx.session_id, fx.player_id, db)
    assert len(encounters) == 1


async def test_get_encounter_rejects_non_member(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """An outsider cannot fetch an encounter's detail."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    with pytest.raises(HTTPException) as exc_info:
        await service.get_encounter(encounter.id, fx.outsider_id, db)
    assert exc_info.value.status_code == 403
