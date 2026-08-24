"""Shared fixtures for handouts tests: async SQLite in-memory database."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.handouts.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.database import Base
from app.sessions.models import Session
from app.storage.base import StorageService

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


class FakeStorageService(StorageService):
    """In-memory StorageService double — no filesystem I/O in unit tests."""

    def __init__(self) -> None:
        """Start with an empty in-memory file store."""
        self.files: dict[str, bytes] = {}

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Persist *data* under *key* and return it."""
        self.files[key] = data
        return key

    def get_url(self, key: str) -> str:
        """Return a deterministic fake URL for *key*."""
        return f"/fake-files/{key}"

    def delete(self, key: str) -> None:
        """Remove *key* from the in-memory store."""
        self.files.pop(key, None)


class _CampaignFixture:
    """A campaign with a DM user, a player user, and a session."""

    def __init__(
        self,
        campaign_id: uuid.UUID,
        session_id: uuid.UUID,
        dm_id: uuid.UUID,
        player_id: uuid.UUID,
    ) -> None:
        self.campaign_id = campaign_id
        self.session_id = session_id
        self.dm_id = dm_id
        self.player_id = player_id


@pytest.fixture
async def campaign_with_session(db: AsyncSession) -> _CampaignFixture:
    """Seed a campaign with a DM, a player, and one game session."""
    dm = User(email="dm@example.com", username="dm", hashed_password="x")
    player = User(email="player@example.com", username="player", hashed_password="x")
    db.add_all([dm, player])
    await db.flush()

    campaign = Campaign(name="Waterdeep", owner_id=dm.id)
    db.add(campaign)
    await db.flush()

    db.add_all(
        [
            CampaignMember(
                campaign_id=campaign.id, user_id=dm.id, role=CampaignRole.dm
            ),
            CampaignMember(
                campaign_id=campaign.id, user_id=player.id, role=CampaignRole.player
            ),
        ]
    )

    session = Session(campaign_id=campaign.id, session_number=1, title="Session 1")
    db.add(session)
    await db.commit()

    return _CampaignFixture(
        campaign_id=campaign.id,
        session_id=session.id,
        dm_id=dm.id,
        player_id=player.id,
    )
