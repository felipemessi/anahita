"""Integration tests for the campaigns HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an httpx client wired to the FastAPI app with an isolated DB."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


async def _register_and_login(
    client: AsyncClient, email: str = "dm@example.com"
) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "pass1234"},
    )
    login_resp = await client.post(
        "/auth/login", json={"email": email, "password": "pass1234"}
    )
    token: str = login_resp.json()["access_token"]
    return token


async def test_create_campaign_requires_auth(client: AsyncClient) -> None:
    """Creating a campaign without a bearer token is rejected."""
    resp = await client.post("/campaigns", json={"name": "No Auth"})
    assert resp.status_code in (401, 403)


async def test_create_campaign_returns_created_campaign(client: AsyncClient) -> None:
    """A logged-in user can create a campaign and gets it back with owner_id set."""
    token = await _register_and_login(client)
    resp = await client.post(
        "/campaigns",
        json={"name": "Lost Mine of Phandelver", "setting": "Sword Coast"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Lost Mine of Phandelver"
    assert body["setting"] == "Sword Coast"
    assert body["status"] == "active"
    assert body["owner_id"]
