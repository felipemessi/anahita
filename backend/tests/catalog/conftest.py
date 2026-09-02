"""Shared fixtures for catalog tests using an in-memory SQLite database."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Import catalog models (and the domains that reference them, transitively
# including *their* FK targets) so Base.metadata includes every table
# exercised by the delete/reference tests.
import app.auth.models  # noqa: F401
import app.campaigns.models  # noqa: F401
import app.catalog.models  # noqa: F401
import app.characters.models  # noqa: F401
import app.combat.models  # noqa: F401
import app.inventory.models  # noqa: F401
import app.maps.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401
import app.world.models  # noqa: F401
from app.database import Base


@pytest_asyncio.fixture
async def db() -> AsyncSession:  # type: ignore[misc]
    """Yield an async SQLite session with all catalog tables created."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session

    await engine.dispose()
