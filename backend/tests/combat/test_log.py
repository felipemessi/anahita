"""Tests for the combat log (backlog Fase 2 história 4)."""

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


async def test_log_records_actions_in_chronological_order(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A sequence of actions produces log entries in the order they happened."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=10, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    await service.update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        EncounterParticipantUpdate(hit_point_current=3),
        db,
    )
    await service.live_update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        hit_point_current=None,
        temporary_hit_points=None,
        armor_class=None,
        add_condition="prone",
        remove_condition=None,
        db=db,
    )
    await service.end_encounter(encounter.id, fx.dm_id, db)

    log = await service.get_log(encounter.id, fx.dm_id, db)

    assert [entry.description for entry in log] == [
        "Goblin joined the encounter",
        "Goblin took 4 damage",
        "Goblin gained condition: prone",
        "Encounter ended",
    ]
    # created_at is strictly non-decreasing in the order returned.
    timestamps = [entry.created_at for entry in log]
    assert timestamps == sorted(timestamps)


async def test_damage_log_entry_records_amount(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A damage log entry carries the exact amount dealt."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=10, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    await service.live_update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        hit_point_current=2,
        temporary_hit_points=None,
        armor_class=None,
        add_condition=None,
        remove_condition=None,
        db=db,
    )

    log = await service.get_log(encounter.id, fx.dm_id, db)
    damage_entry = next(e for e in log if e.damage_dealt is not None)
    assert damage_entry.damage_dealt == 5
    assert damage_entry.target_id == participant_id


async def test_log_survives_participant_removal(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Removing a participant nulls the log's references but keeps the entries."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )
    encounter = await service.add_participant(
        encounter.id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Goblin", initiative=10, hit_point_max=7, armor_class=15, turn_order=0
        ),
        db,
    )
    participant_id = encounter.participants[0].id

    await service.remove_participant(encounter.id, participant_id, fx.dm_id, db)

    log = await service.get_log(encounter.id, fx.dm_id, db)
    descriptions = [entry.description for entry in log]
    assert "Goblin joined the encounter" in descriptions
    assert "Goblin left the encounter" in descriptions


async def test_get_log_rejects_non_member(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """An outsider cannot read an encounter's combat log."""
    fx = campaign_with_session
    service = CombatService()
    encounter = await service.create_encounter(
        fx.session_id, fx.dm_id, EncounterCreate(name="Ambush"), db
    )

    with pytest.raises(HTTPException) as exc_info:
        await service.get_log(encounter.id, fx.outsider_id, db)
    assert exc_info.value.status_code == 403
