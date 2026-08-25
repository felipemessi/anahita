"""Integration tests for CombatService.declare_action and roll_initiative rolling."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.models import (
    ClassDefinition,
    Item,
    Monster,
    MonsterAction,
    Race,
    Spell,
)
from app.catalog.seeds.seed import seed_catalog
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
    CharacterEquipmentCreate,
    CharacterSpellCreate,
)
from app.characters.service import CharacterService
from app.combat.models import Encounter, EncounterParticipant
from app.combat.schemas import (
    EncounterCreate,
    EncounterParticipantCreate,
    WSDeclareActionPayload,
)
from app.combat.service import CombatService
from app.database import Base
from app.sessions.domain import SessionStatus
from app.sessions.models import Session

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Provide an isolated async SQLite session, catalog seeded."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        await seed_catalog(session)
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class _Fixture:
    """A campaign/session with DM/player/outsider, a fighter PC, and an encounter."""

    def __init__(
        self,
        session_id: uuid.UUID,
        dm_id: uuid.UUID,
        player_id: uuid.UUID,
        outsider_id: uuid.UUID,
        character_id: uuid.UUID,
        equipment_id: uuid.UUID,
    ) -> None:
        self.session_id = session_id
        self.dm_id = dm_id
        self.player_id = player_id
        self.outsider_id = outsider_id
        self.character_id = character_id
        self.equipment_id = equipment_id


_STANDARD_ARRAY = [
    CharacterAbilityScoreCreate(ability="str", base_score=16),  # +3
    CharacterAbilityScoreCreate(ability="dex", base_score=14),  # +2
    CharacterAbilityScoreCreate(ability="con", base_score=13),
    CharacterAbilityScoreCreate(ability="int", base_score=10),
    CharacterAbilityScoreCreate(ability="wis", base_score=10),
    CharacterAbilityScoreCreate(ability="cha", base_score=8),
]


@pytest.fixture
async def fixture_with_fighter(db: AsyncSession) -> _Fixture:
    """Set up a fighter PC equipped with a Longsword (STR weapon) in an encounter."""
    dm = User(email="dm@example.com", username="dm", hashed_password="x")
    player = User(email="player@example.com", username="player", hashed_password="x")
    outsider = User(
        email="outsider@example.com", username="outsider", hashed_password="x"
    )
    db.add_all([dm, player, outsider])
    await db.flush()

    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()
    dm_member = CampaignMember(
        campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm
    )
    player_member = CampaignMember(
        campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
    )
    db.add_all([dm_member, player_member])
    await db.flush()

    session = Session(
        campaign_id=campaign.id,
        session_number=1,
        title="Session 1",
        status=SessionStatus.planned,
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    await db.refresh(player_member)

    race_result = await db.execute(select(Race).where(Race.index == "human"))
    race_id = race_result.scalar_one().id
    class_result = await db.execute(
        select(ClassDefinition).where(ClassDefinition.index == "fighter")
    )
    class_id = class_result.scalar_one().id
    item_result = await db.execute(select(Item).where(Item.index == "longsword"))
    longsword_id = item_result.scalar_one().id

    char_service = CharacterService()
    character = await char_service.create_character(
        player.id,
        CharacterCreate(
            campaign_member_id=player_member.id,
            name="Aldric",
            race_id=race_id,
            ability_scores=_STANDARD_ARRAY,
            classes=[CharacterClassCreate(class_definition_id=class_id)],
        ),
        db,
    )
    character = await char_service.add_equipment(
        character.id,
        player.id,
        CharacterEquipmentCreate(item_id=longsword_id, equipped=True),
        db,
    )
    equipment_id = character.equipment[0].id

    combat_service = CombatService()
    encounter = await combat_service.create_encounter(
        session.id, dm.id, EncounterCreate(name="Ambush"), db
    )
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            character_id=character.id,
            name="Aldric",
            hit_point_max=character.hit_point_max,
            armor_class=character.armor_class,
            turn_order=0,
        ),
        db,
    )
    goblin_result = await db.execute(select(Monster).where(Monster.index == "goblin"))
    goblin = goblin_result.scalar_one()
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            monster_id=goblin.id,
            name="Goblin",
            hit_point_max=7,
            armor_class=15,
            turn_order=1,
        ),
        db,
    )

    return _Fixture(
        session_id=session.id,
        dm_id=dm.id,
        player_id=player.id,
        outsider_id=outsider.id,
        character_id=character.id,
        equipment_id=equipment_id,
    )


async def _get_encounter_id(db: AsyncSession, session_id: uuid.UUID) -> uuid.UUID:
    result = await db.execute(
        select(Encounter).where(Encounter.session_id == session_id)
    )
    return result.scalar_one().id


async def _participant_ids(
    db: AsyncSession, encounter_id: uuid.UUID
) -> dict[str, uuid.UUID]:
    result = await db.execute(
        select(EncounterParticipant).where(
            EncounterParticipant.encounter_id == encounter_id
        )
    )
    return {p.name: p.id for p in result.scalars().all()}


async def test_declare_weapon_attack_hits_and_applies_damage(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A weapon attack that hits rolls (or takes manual) damage and applies it."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="attack_weapon",
            weapon_equipment_id=fx.equipment_id,
            manual_attack_roll=20,  # guaranteed hit vs AC 15
            manual_damage_roll=6,
        ),
        db,
    )
    assert result.hit is True
    # STR 16 -> +3 mod; Fighter level 1 proficiency bonus +2.
    assert result.attack_bonus == 5
    assert result.damage_rolled == 6
    assert result.damage_type == "slashing"

    encounter = await service.get_encounter(encounter_id, fx.dm_id, db)
    goblin = next(p for p in encounter.participants if p.name == "Goblin")
    assert goblin.hit_point_current == 1


async def test_declare_weapon_attack_misses_no_damage(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A weapon attack roll below target AC misses and deals no damage."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="attack_weapon",
            weapon_equipment_id=fx.equipment_id,
            manual_attack_roll=1,  # guaranteed miss vs AC 15
        ),
        db,
    )
    assert result.hit is False
    assert result.damage_rolled is None

    encounter = await service.get_encounter(encounter_id, fx.dm_id, db)
    goblin = next(p for p in encounter.participants if p.name == "Goblin")
    assert goblin.hit_point_current == 7


async def test_declare_action_wrong_owner_rejected(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """An outsider cannot declare an action for someone else's participant."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.outsider_id,
            WSDeclareActionPayload(
                participant_id=ids["Aldric"],
                target_id=ids["Goblin"],
                action_type="attack_weapon",
                weapon_equipment_id=fx.equipment_id,
                manual_attack_roll=20,
                manual_damage_roll=5,
            ),
            db,
        )
    assert exc.value.status_code == 403


async def test_declare_monster_attack_uses_stat_block(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A monster's attack resolves bonus/damage from its catalog action. DM only."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    goblin_result = await db.execute(select(Monster).where(Monster.index == "goblin"))
    goblin = goblin_result.scalar_one()
    action_result = await db.execute(
        select(MonsterAction).where(
            MonsterAction.monster_id == goblin.id, MonsterAction.name == "Scimitar"
        )
    )
    scimitar = action_result.scalar_one()


    result = await service.declare_action(
        encounter_id,
        fx.dm_id,
        WSDeclareActionPayload(
            participant_id=ids["Goblin"],
            target_id=ids["Aldric"],
            action_type="attack_weapon",
            monster_action_id=scimitar.id,
            manual_attack_roll=20,
        ),
        db,
    )
    assert result.attack_bonus == 4
    assert result.hit is True
    assert result.damage_rolled is not None
    assert result.damage_type == "slashing"


async def test_declare_grapple_success_applies_condition(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A successful grapple applies the `grappled` condition to the target."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="grapple",
            manual_attack_roll=20,
            manual_target_roll=1,
        ),
        db,
    )
    assert result.hit is True
    assert result.condition_applied == "grappled"

    encounter = await service.get_encounter(encounter_id, fx.dm_id, db)
    goblin = next(p for p in encounter.participants if p.name == "Goblin")
    assert any(c.condition == "grappled" for c in goblin.conditions)


async def test_declare_grapple_failure_no_condition(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A failed grapple contest doesn't apply the `grappled` condition."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="grapple",
            manual_attack_roll=1,
            manual_target_roll=20,
        ),
        db,
    )
    assert result.hit is False
    assert result.condition_applied is None


async def test_declare_action_manual_participant_requires_manual_bonus(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A purely manual participant (no character/monster link) needs manual bonuses."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    await service.add_participant(
        encounter_id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Mystery Foe", hit_point_max=5, armor_class=10, turn_order=2
        ),
        db,
    )
    updated = await service.get_encounter(encounter_id, fx.dm_id, db)
    mystery_id = next(
        p.id for p in updated.participants if p.name == "Mystery Foe"
    )


    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.dm_id,
            WSDeclareActionPayload(
                participant_id=mystery_id,
                target_id=ids["Aldric"],
                action_type="attack_weapon",
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_declare_spell_attack_resolves_catalog_damage(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A cantrip attack resolves its attack bonus and catalog SpellDamage."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)

    race_result = await db.execute(select(Race).where(Race.index == "human"))
    race_id = race_result.scalar_one().id
    class_result = await db.execute(
        select(ClassDefinition).where(ClassDefinition.index == "wizard")
    )
    wizard_class_id = class_result.scalar_one().id
    spell_result = await db.execute(select(Spell).where(Spell.index == "fire-bolt"))
    fire_bolt_id = spell_result.scalar_one().id

    campaign_result = await db.execute(
        select(CampaignMember).where(CampaignMember.user_id == fx.player_id)
    )
    player_member = campaign_result.scalar_one()

    char_service = CharacterService()
    wizard = await char_service.create_character(
        fx.player_id,
        CharacterCreate(
            campaign_member_id=player_member.id,
            name="Elowen",
            race_id=race_id,
            ability_scores=_STANDARD_ARRAY,
            classes=[CharacterClassCreate(class_definition_id=wizard_class_id)],
        ),
        db,
    )
    wizard = await char_service.add_spell(
        wizard.id,
        fx.player_id,
        CharacterSpellCreate(spell_id=fire_bolt_id, source_class="wizard"),
        db,
    )
    spell_entry_id = wizard.spells[0].id

    combat_service = CombatService()
    await combat_service.add_participant(
        encounter_id,
        fx.dm_id,
        EncounterParticipantCreate(
            character_id=wizard.id,
            name="Elowen",
            hit_point_max=wizard.hit_point_max,
            armor_class=wizard.armor_class,
            turn_order=2,
        ),
        db,
    )


    result = await combat_service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=(await _participant_ids(db, encounter_id))["Elowen"],
            target_id=ids["Goblin"],
            action_type="attack_spell",
            spell_entry_id=spell_entry_id,
            manual_attack_roll=20,
        ),
        db,
    )
    assert result.hit is True
    # INT 10 -> +0 mod; Wizard level 1 proficiency bonus +2.
    assert result.attack_bonus == 2
    assert result.damage_rolled is not None
    assert result.damage_type == "fire"


async def test_roll_initiative_server_rolls_for_character(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """Omitting initiative rolls 1d20 + DEX modifier server-side for a Character."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()


    participant = await service.roll_initiative(
        encounter_id, ids["Aldric"], fx.player_id, None, db
    )
    # DEX 14 -> +2 mod; a d20 roll is always within [1, 20].
    assert participant.initiative is not None
    assert 3 <= participant.initiative <= 22


async def test_roll_initiative_manual_participant_requires_value(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A manual participant has no DEX to roll from — omitting initiative fails."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    service = CombatService()

    await service.add_participant(
        encounter_id,
        fx.dm_id,
        EncounterParticipantCreate(
            name="Mystery Foe", hit_point_max=5, armor_class=10, turn_order=2
        ),
        db,
    )
    ids = await _participant_ids(db, encounter_id)

    with pytest.raises(HTTPException) as exc:
        await service.roll_initiative(
            encounter_id, ids["Mystery Foe"], fx.dm_id, None, db
        )
    assert exc.value.status_code == 422


async def test_declare_action_manual_roll_logged_as_not_rolled_by_system(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A manually-typed attack roll is logged with rolled_by_system=False."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="attack_weapon",
            weapon_equipment_id=fx.equipment_id,
            manual_attack_roll=20,
            manual_damage_roll=5,
        ),
        db,
    )
    log = await service.get_log(encounter_id, fx.dm_id, db)
    attack_entry = next(entry for entry in log if entry.action_type == "attack_weapon")
    assert attack_entry.rolled_by_system is False


async def test_declare_action_auto_roll_logged_as_rolled_by_system(
    db: AsyncSession, fixture_with_fighter: _Fixture
) -> None:
    """A server-rolled attack is logged with rolled_by_system=True."""
    fx = fixture_with_fighter
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Aldric"],
            target_id=ids["Goblin"],
            action_type="attack_weapon",
            weapon_equipment_id=fx.equipment_id,
        ),
        db,
    )
    log = await service.get_log(encounter_id, fx.dm_id, db)
    attack_entry = next(entry for entry in log if entry.action_type == "attack_weapon")
    assert attack_entry.rolled_by_system is True
