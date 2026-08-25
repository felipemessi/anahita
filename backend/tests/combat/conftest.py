"""Shared fixtures for combat tests: async SQLite in-memory database."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime

import pytest
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
from app.characters.models import Character
from app.database import Base
from app.sessions.domain import SessionStatus
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
    """A campaign with a DM user, a player user, and a session, ready for combat."""

    def __init__(
        self,
        campaign_id: uuid.UUID,
        session_id: uuid.UUID,
        dm_id: uuid.UUID,
        player_id: uuid.UUID,
        outsider_id: uuid.UUID,
        player_character_id: uuid.UUID | None = None,
    ) -> None:
        self.campaign_id = campaign_id
        self.session_id = session_id
        self.dm_id = dm_id
        self.player_id = player_id
        self.outsider_id = outsider_id
        self.player_character_id = player_character_id


@pytest.fixture
async def campaign_with_session(db: AsyncSession) -> _CampaignFixture:
    """Seed a campaign with a DM, a player, an outsider, and one game session."""
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

    db.add_all(
        [
            CampaignMember(campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
        ]
    )

    session = Session(
        campaign_id=campaign.id,
        session_number=1,
        title="Session 1",
        status=SessionStatus.planned,
        created_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()

    return _CampaignFixture(
        campaign_id=campaign.id,
        session_id=session.id,
        dm_id=dm.id,
        player_id=player.id,
        outsider_id=outsider.id,
    )


@pytest.fixture
async def campaign_with_pc(
    db: AsyncSession, campaign_with_session: _CampaignFixture
) -> _CampaignFixture:
    """Extend `campaign_with_session` with a Character for the player's PC.

    Built directly via the ORM (not `CharacterService`) — SQLite tests don't
    enforce FK constraints, so `race_id` doesn't need a real catalog row for
    this fixture's purposes (combat's PC-population logic only reads
    `Character`'s own columns).
    """
    fx = campaign_with_session
    result = await db.execute(
        select(CampaignMember).where(
            CampaignMember.campaign_id == fx.campaign_id,
            CampaignMember.user_id == fx.player_id,
        )
    )
    player_member = result.scalar_one()

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

    return _CampaignFixture(
        campaign_id=fx.campaign_id,
        session_id=fx.session_id,
        dm_id=fx.dm_id,
        player_id=fx.player_id,
        outsider_id=fx.outsider_id,
        player_character_id=character.id,
    )
