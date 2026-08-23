"""Tests for condition -> mechanical effect resolution (backlog Fase 2 história 3)."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.combat.schemas import EncounterCreate, EncounterParticipantCreate
from app.combat.service import CombatService
from tests.combat.conftest import _CampaignFixture


async def test_blinded_participant_has_attack_disadvantage_effect(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """A blinded participant's read includes the attack_disadvantage effect."""
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
    assert encounter.participants[0].effects == []

    participant = await service.live_update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        hit_point_current=None,
        temporary_hit_points=None,
        armor_class=None,
        add_condition="blinded",
        remove_condition=None,
        db=db,
    )

    effect_types = {e.effect_type for e in participant.effects}
    assert "attack_disadvantage" in effect_types
    assert "attacks_against_advantage" in effect_types
    assert "auto_fail_save" in effect_types
    assert any(c.condition == "blinded" for c in participant.conditions)


async def test_removing_condition_clears_its_effects(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Removing a participant's only condition clears its resolved effects too."""
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
        hit_point_current=None,
        temporary_hit_points=None,
        armor_class=None,
        add_condition="prone",
        remove_condition=None,
        db=db,
    )
    participant = await service.live_update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        hit_point_current=None,
        temporary_hit_points=None,
        armor_class=None,
        add_condition=None,
        remove_condition="prone",
        db=db,
    )

    assert participant.conditions == []
    assert participant.effects == []


async def test_exhaustion_level_one_gives_ability_check_disadvantage(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> None:
    """Exhaustion (resolved at level 1) yields an ability_check_disadvantage effect."""
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

    participant = await service.live_update_participant(
        encounter.id,
        participant_id,
        fx.dm_id,
        hit_point_current=None,
        temporary_hit_points=None,
        armor_class=None,
        add_condition="exhaustion",
        remove_condition=None,
        db=db,
    )

    effect_types = {e.effect_type for e in participant.effects}
    assert "ability_check_disadvantage" in effect_types
    # Not severe enough (level defaults to 1) to trigger the level-4+ effects.
    assert "hp_max_halved" not in effect_types
