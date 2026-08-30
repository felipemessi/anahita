"""Integration tests for `CombatService.declare_action`'s `use_class_resource`.

Covers backlog Fase 12 história 1 — a class resource that generates an
action (Channel Divinity: Turn Undead) both consumes the resource *and*
resolves its mechanical effect in one `declare_action` call, instead of
only ever bumping `CharacterResource.used`.
"""

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
    Feature,
    Monster,
    Race,
    SubclassDefinition,
)
from app.catalog.seeds.seed import seed_catalog
from app.characters.models import CharacterResource
from app.characters.schemas import (
    CharacterAbilityScoreCreate,
    CharacterClassCreate,
    CharacterCreate,
)
from app.characters.service import CharacterService
from app.combat.models import Encounter, EncounterCondition, EncounterParticipant
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

# Cleric of Life, level 2: WIS 16 (+3 mod) + proficiency +2 -> spell save DC 13.
_CLERIC_ABILITY_SCORES = [
    CharacterAbilityScoreCreate(ability="str", base_score=10),
    CharacterAbilityScoreCreate(ability="dex", base_score=12),
    CharacterAbilityScoreCreate(ability="con", base_score=13),
    CharacterAbilityScoreCreate(ability="int", base_score=10),
    CharacterAbilityScoreCreate(ability="wis", base_score=16),
    CharacterAbilityScoreCreate(ability="cha", base_score=8),
]
_CLERIC_SAVE_DC = 13


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
    """A campaign/session with a level-2 Cleric of Life PC and a Skeleton, in combat."""

    def __init__(
        self,
        session_id: uuid.UUID,
        dm_id: uuid.UUID,
        player_id: uuid.UUID,
        character_id: uuid.UUID,
    ) -> None:
        self.session_id = session_id
        self.dm_id = dm_id
        self.player_id = player_id
        self.character_id = character_id


@pytest.fixture
async def fixture_with_cleric(db: AsyncSession) -> _Fixture:
    """Set up a level-2 Cleric of Life PC, a Skeleton, and a Goblin, in an encounter."""
    dm = User(email="dm@example.com", username="dm", hashed_password="x")
    player = User(email="player@example.com", username="player", hashed_password="x")
    db.add_all([dm, player])
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
        select(ClassDefinition).where(ClassDefinition.index == "cleric")
    )
    class_id = class_result.scalar_one().id
    subclass_result = await db.execute(
        select(SubclassDefinition).where(SubclassDefinition.index == "life")
    )
    subclass_id = subclass_result.scalar_one().id

    char_service = CharacterService()
    character = await char_service.create_character(
        player.id,
        CharacterCreate(
            campaign_member_id=player_member.id,
            name="Seraphine",
            race_id=race_id,
            ability_scores=_CLERIC_ABILITY_SCORES,
            classes=[
                CharacterClassCreate(
                    class_definition_id=class_id, subclass_id=subclass_id, level=2
                )
            ],
        ),
        db,
    )

    combat_service = CombatService()
    encounter = await combat_service.create_encounter(
        session.id, dm.id, EncounterCreate(name="Crypt"), db
    )
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            character_id=character.id,
            name="Seraphine",
            hit_point_max=character.hit_point_max,
            armor_class=character.armor_class,
            turn_order=0,
        ),
        db,
    )
    skeleton_result = await db.execute(
        select(Monster).where(Monster.index == "skeleton")
    )
    skeleton = skeleton_result.scalar_one()
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            monster_id=skeleton.id,
            name="Skeleton",
            hit_point_max=13,
            armor_class=13,
            turn_order=1,
        ),
        db,
    )
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            monster_id=skeleton.id,
            name="Skeleton 2",
            hit_point_max=13,
            armor_class=13,
            turn_order=2,
        ),
        db,
    )
    await combat_service.add_participant(
        encounter.id,
        dm.id,
        EncounterParticipantCreate(
            name="Mystery Assailant",  # manual participant, no stat block
            hit_point_max=10,
            armor_class=12,
            turn_order=3,
        ),
        db,
    )

    return _Fixture(
        session_id=session.id,
        dm_id=dm.id,
        player_id=player.id,
        character_id=character.id,
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


async def _turn_undead_option_id(db: AsyncSession) -> uuid.UUID:
    result = await db.execute(
        select(Feature).where(Feature.index == "channel-divinity-turn-undead")
    )
    return result.scalar_one().id


async def _resource_used(db: AsyncSession, character_id: uuid.UUID) -> int:
    result = await db.execute(
        select(CharacterResource).where(
            CharacterResource.character_id == character_id,
            CharacterResource.resource_key == "channel_divinity_charges",
        )
    )
    entry = result.scalar_one_or_none()
    return entry.used if entry is not None else 0


async def test_turn_undead_consumes_resource_and_frightens_on_failed_save(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A failed Wisdom save applies `frightened` and the charge is spent."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Seraphine"],
            target_id=ids["Skeleton"],
            action_type="use_class_resource",
            resource_key="channel_divinity_charges",
            resource_option_id=option_id,
            manual_save_rolls={ids["Skeleton"]: 1},  # guaranteed fail vs DC 13
        ),
        db,
    )

    assert result.resource_key == "channel_divinity_charges"
    assert len(result.resource_targets) == 1
    outcome = result.resource_targets[0]
    assert outcome.participant_id == ids["Skeleton"]
    assert outcome.save_dc == _CLERIC_SAVE_DC
    assert outcome.succeeded is False
    assert outcome.condition_applied == "frightened"

    assert await _resource_used(db, fx.character_id) == 1

    condition_result = await db.execute(
        select(EncounterCondition).where(
            EncounterCondition.participant_id == ids["Skeleton"]
        )
    )
    conditions = condition_result.scalars().all()
    assert len(conditions) == 1
    assert conditions[0].condition.value == "frightened"
    assert conditions[0].duration_rounds == 10


async def test_turn_undead_no_condition_on_successful_save(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A successful Wisdom save applies no condition, but still spends the charge."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Seraphine"],
            target_id=ids["Skeleton"],
            action_type="use_class_resource",
            resource_key="channel_divinity_charges",
            resource_option_id=option_id,
            manual_save_rolls={ids["Skeleton"]: 20},  # guaranteed success vs DC 13
        ),
        db,
    )

    outcome = result.resource_targets[0]
    assert outcome.succeeded is True
    assert outcome.condition_applied is None
    assert await _resource_used(db, fx.character_id) == 1

    condition_result = await db.execute(
        select(EncounterCondition).where(
            EncounterCondition.participant_id == ids["Skeleton"]
        )
    )
    assert condition_result.scalars().all() == []


async def test_turn_undead_resolves_multiple_explicit_targets(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """`additional_target_ids` lets one Turn Undead use hit more than one undead.

    Deliberate simplification (backlog Fase 12): no area/map geometry yet, so
    "every undead within 30 feet" becomes "whichever participants the client
    explicitly lists" rather than an automatic radius search.
    """
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Seraphine"],
            target_id=ids["Skeleton"],
            additional_target_ids=[ids["Skeleton 2"]],
            action_type="use_class_resource",
            resource_key="channel_divinity_charges",
            resource_option_id=option_id,
            manual_save_rolls={ids["Skeleton"]: 1, ids["Skeleton 2"]: 20},
        ),
        db,
    )

    assert await _resource_used(db, fx.character_id) == 1  # one use, many targets
    outcomes = {o.participant_id: o for o in result.resource_targets}
    assert outcomes[ids["Skeleton"]].condition_applied == "frightened"
    assert outcomes[ids["Skeleton 2"]].condition_applied is None


async def test_turn_undead_manual_participant_target_requires_manual_save_roll(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A target with no stat block (manual participant) needs a manual save roll."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.player_id,
            WSDeclareActionPayload(
                participant_id=ids["Seraphine"],
                target_id=ids["Mystery Assailant"],
                action_type="use_class_resource",
                resource_key="channel_divinity_charges",
                resource_option_id=option_id,
            ),
            db,
        )
    assert exc.value.status_code == 422

    # Supplying the manual roll resolves it fine.
    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Seraphine"],
            target_id=ids["Mystery Assailant"],
            action_type="use_class_resource",
            resource_key="channel_divinity_charges",
            resource_option_id=option_id,
            manual_save_rolls={ids["Mystery Assailant"]: 1},
        ),
        db,
    )
    assert result.resource_targets[0].succeeded is False


async def test_use_class_resource_without_mapped_effect_is_bookkeeping_only(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A resource use with no mapped effect just spends the charge — no targets."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    preserve_life_result = await db.execute(
        select(Feature).where(Feature.index == "channel-divinity-preserve-life")
    )
    preserve_life_id = preserve_life_result.scalar_one().id
    service = CombatService()

    result = await service.declare_action(
        encounter_id,
        fx.player_id,
        WSDeclareActionPayload(
            participant_id=ids["Seraphine"],
            target_id=ids["Skeleton"],
            action_type="use_class_resource",
            resource_key="channel_divinity_charges",
            resource_option_id=preserve_life_id,
        ),
        db,
    )

    assert result.resource_key == "channel_divinity_charges"
    assert result.resource_targets == []
    assert await _resource_used(db, fx.character_id) == 1

    condition_result = await db.execute(
        select(EncounterCondition).where(
            EncounterCondition.participant_id == ids["Skeleton"]
        )
    )
    assert condition_result.scalars().all() == []


async def test_use_class_resource_requires_resource_key(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A missing `resource_key` is a clear 422, not a crash."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.player_id,
            WSDeclareActionPayload(
                participant_id=ids["Seraphine"],
                target_id=ids["Skeleton"],
                action_type="use_class_resource",
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_use_class_resource_requires_a_character_attacker(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """A monster/manual participant has no class resource to spend — clear 422."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.dm_id,
            WSDeclareActionPayload(
                participant_id=ids["Skeleton"],
                target_id=ids["Seraphine"],
                action_type="use_class_resource",
                resource_key="channel_divinity_charges",
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_use_class_resource_option_required_when_character_has_several(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """`CharacterService.use_resource`'s own option_id requirement still applies."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    service = CombatService()

    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.player_id,
            WSDeclareActionPayload(
                participant_id=ids["Seraphine"],
                target_id=ids["Skeleton"],
                action_type="use_class_resource",
                resource_key="channel_divinity_charges",
            ),
            db,
        )
    assert exc.value.status_code == 422


async def test_use_class_resource_dm_cannot_spend_a_players_resource(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """Unlike attacks/contests, the DM can't declare this on a player's behalf.

    `CharacterService.use_resource` is owner-only — `declare_action`
    delegates to it as-is rather than special-casing the DM, so this 403
    is a deliberate (documented) inherited restriction, not a bug.
    """
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id,
            fx.dm_id,
            WSDeclareActionPayload(
                participant_id=ids["Seraphine"],
                target_id=ids["Skeleton"],
                action_type="use_class_resource",
                resource_key="channel_divinity_charges",
                resource_option_id=option_id,
                manual_save_rolls={ids["Skeleton"]: 1},
            ),
            db,
        )
    assert exc.value.status_code == 403


async def test_use_class_resource_no_uses_remaining_is_a_clear_422(
    db: AsyncSession, fixture_with_cleric: _Fixture
) -> None:
    """Spending past the resource's limit still fails clearly through combat."""
    fx = fixture_with_cleric
    encounter_id = await _get_encounter_id(db, fx.session_id)
    ids = await _participant_ids(db, encounter_id)
    option_id = await _turn_undead_option_id(db)
    service = CombatService()

    payload_kwargs = dict(
        participant_id=ids["Seraphine"],
        target_id=ids["Skeleton"],
        action_type="use_class_resource",
        resource_key="channel_divinity_charges",
        resource_option_id=option_id,
        manual_save_rolls={ids["Skeleton"]: 20},
    )
    # Level 2 Channel Divinity: 1 use between rests.
    await service.declare_action(
        encounter_id, fx.player_id, WSDeclareActionPayload(**payload_kwargs), db
    )
    with pytest.raises(HTTPException) as exc:
        await service.declare_action(
            encounter_id, fx.player_id, WSDeclareActionPayload(**payload_kwargs), db
        )
    assert exc.value.status_code == 422
