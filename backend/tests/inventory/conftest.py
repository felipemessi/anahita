"""Shared fixtures for inventory tests: async SQLite in-memory database."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.inventory.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.catalog.models import EquipmentCategory, Item, MagicItem
from app.characters.models import Character
from app.combat.models import Encounter
from app.database import Base
from app.sessions.models import Session

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession]:
    """Provide an isolated async SQLite session with all tables created."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


class _CampaignFixture:
    """A campaign with a DM, a player + character, an encounter, and a catalog item."""

    def __init__(
        self,
        campaign_id: uuid.UUID,
        session_id: uuid.UUID,
        encounter_id: uuid.UUID,
        dm_id: uuid.UUID,
        player_id: uuid.UUID,
        character_id: uuid.UUID,
        item_id: uuid.UUID,
        magic_item_id: uuid.UUID,
    ) -> None:
        self.campaign_id = campaign_id
        self.session_id = session_id
        self.encounter_id = encounter_id
        self.dm_id = dm_id
        self.player_id = player_id
        self.character_id = character_id
        self.item_id = item_id
        self.magic_item_id = magic_item_id


@pytest.fixture
async def campaign_with_encounter(db: AsyncSession) -> _CampaignFixture:
    """Seed a campaign with a DM, a player + character, an encounter, and an item."""
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

    session = Session(campaign_id=campaign.id, session_number=1, title="Session 1")
    db.add(session)
    await db.flush()

    encounter = Encounter(session_id=session.id, name="Ambush")
    db.add(encounter)

    category = EquipmentCategory(index="gear", is_custom=False)
    db.add(category)
    await db.flush()

    item = Item(
        item_type="gear",
        equipment_category_id=category.id,
        weight=1.0,
        cost=10,
        is_custom=False,
    )
    db.add(item)
    await db.flush()

    magic_item = MagicItem(
        equipment_category_id=category.id,
        rarity="rare",
        is_custom=False,
    )
    db.add(magic_item)
    await db.flush()

    character = Character(
        campaign_member_id=player_member.id,
        name="Aria",
        race_id=uuid.uuid4(),
        level=1,
        hit_point_max=10,
        hit_point_current=10,
        armor_class=12,
        speed=30,
        proficiency_bonus=2,
    )
    db.add(character)
    await db.commit()

    return _CampaignFixture(
        campaign_id=campaign.id,
        session_id=session.id,
        encounter_id=encounter.id,
        dm_id=dm.id,
        player_id=player.id,
        character_id=character.id,
        item_id=item.id,
        magic_item_id=magic_item.id,
    )
