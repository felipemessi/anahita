"""Postgres-only integration test for cross-entity world search (tsvector).

Skipped automatically when a real Postgres instance isn't reachable — SQLite
(used by the rest of the world test suite) doesn't support
`tsvector`/`plainto_tsquery`, so this query can only be exercised here.
"""

import os
import uuid
from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.models import User
from app.campaigns.domain import CampaignRole
from app.campaigns.models import Campaign, CampaignMember
from app.queries.world_queries import search_world_entities
from app.wiki.models import WikiPage
from app.world.models import NPC, Faction, Location

pytestmark = pytest.mark.postgres

_DATABASE_URL = os.environ.get(
    "TEST_POSTGRES_URL", "postgresql+asyncpg://user:pass@localhost:5432/anahita"
)


@pytest.fixture
async def pg_db() -> AsyncGenerator[AsyncSession]:
    """Yield a session against a real Postgres database, or skip if unreachable."""
    engine = create_async_engine(_DATABASE_URL, echo=False)
    try:
        async with engine.connect():
            pass
    except Exception as exc:
        pytest.skip(f"Postgres not reachable at {_DATABASE_URL}: {exc}")

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_search_finds_matches_across_npc_location_faction_and_wiki_page(
    pg_db: AsyncSession,
) -> None:
    """A query term matching all four entity types returns one hit each."""
    marker = f"Gloomhaven-{uuid.uuid4().hex[:8]}"
    user = User(email=f"{marker}@example.com", username=marker, hashed_password="x")
    pg_db.add(user)
    await pg_db.flush()
    campaign = Campaign(name="Search Test Table", owner_id=user.id)
    pg_db.add(campaign)
    await pg_db.flush()
    pg_db.add(
        CampaignMember(campaign_id=campaign.id, user_id=user.id, role=CampaignRole.dm)
    )
    pg_db.add(
        NPC(
            campaign_id=campaign.id,
            name="Innkeeper",
            race="Human",
            description=f"Runs the {marker} tavern",
        )
    )
    pg_db.add(
        Location(
            campaign_id=campaign.id,
            name=marker,
            location_type="town",
            description="A misty town",
        )
    )
    pg_db.add(
        Faction(
            campaign_id=campaign.id,
            name="Cartographers",
            description=f"Mapped every road into {marker}",
        )
    )
    pg_db.add(
        WikiPage(
            campaign_id=campaign.id,
            title=marker,
            slug=marker.lower(),
            content=f"Legends say {marker} was founded by a dragon.",
        )
    )
    await pg_db.commit()

    try:
        hits = await search_world_entities(campaign.id, marker, pg_db)
        assert {hit.entity_type for hit in hits} == {
            "npc",
            "location",
            "faction",
            "wiki_page",
        }

        no_match = await search_world_entities(campaign.id, "no-such-term", pg_db)
        assert no_match == []
    finally:
        await pg_db.execute(delete(NPC).where(NPC.campaign_id == campaign.id))
        await pg_db.execute(delete(Location).where(Location.campaign_id == campaign.id))
        await pg_db.execute(delete(Faction).where(Faction.campaign_id == campaign.id))
        await pg_db.execute(delete(WikiPage).where(WikiPage.campaign_id == campaign.id))
        await pg_db.execute(
            delete(CampaignMember).where(CampaignMember.campaign_id == campaign.id)
        )
        await pg_db.execute(delete(Campaign).where(Campaign.id == campaign.id))
        await pg_db.execute(delete(User).where(User.id == user.id))
        await pg_db.commit()
