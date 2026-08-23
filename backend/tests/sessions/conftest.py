"""Shared fixtures for sessions tests: async SQLite in-memory database."""

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
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
