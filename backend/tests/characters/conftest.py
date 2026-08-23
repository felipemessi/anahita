"""Shared fixtures for characters tests: async SQLite in-memory database."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
from app.catalog.models import ClassDefinition, Race
from app.catalog.seeds.seed import seed_catalog
from app.database import Base

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


@pytest.fixture
async def human_race_id(db: AsyncSession) -> str:
    """Seed the catalog and return the SRD Human race's id."""
    await seed_catalog(db)
    result = await db.execute(select(Race).where(Race.index == "human"))
    return str(result.scalar_one().id)


@pytest.fixture
async def fighter_class_id(db: AsyncSession) -> str:
    """Seed the catalog (idempotent) and return the SRD Fighter class's id."""
    await seed_catalog(db)
    result = await db.execute(
        select(ClassDefinition).where(ClassDefinition.index == "fighter")
    )
    return str(result.scalar_one().id)


@pytest.fixture
async def wizard_class_id(db: AsyncSession) -> str:
    """Seed the catalog (idempotent) and return the SRD Wizard class's id."""
    await seed_catalog(db)
    result = await db.execute(
        select(ClassDefinition).where(ClassDefinition.index == "wizard")
    )
    return str(result.scalar_one().id)
