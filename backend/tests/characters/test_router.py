"""Integration tests for the characters HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
from app.catalog.seeds.seed import seed_catalog
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an httpx client wired to the FastAPI app, seeded catalog, isolated DB."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        async with factory() as seed_session:
            await seed_catalog(seed_session)
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


async def _register_and_login(
    client: AsyncClient, email: str = "player@example.com"
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


_STANDARD_ARRAY = [
    {"ability": "str", "base_score": 15},
    {"ability": "dex", "base_score": 14},
    {"ability": "con", "base_score": 13},
    {"ability": "int", "base_score": 12},
    {"ability": "wis", "base_score": 10},
    {"ability": "cha", "base_score": 8},
]


async def test_create_character_over_http(client: AsyncClient) -> None:
    """A logged-in player can create a character sheet for their own membership."""
    token = await _register_and_login(client)
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    membership_resp = await client.get(
        f"/campaigns/{campaign_id}/members/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert membership_resp.status_code == 200
    campaign_member_id = membership_resp.json()["id"]

    catalog_resp = await client.get("/catalog/races", params={"search": "Human"})
    human_race_id = catalog_resp.json()[0]["id"]
    classes_resp = await client.get("/catalog/classes", params={"search": "Fighter"})
    fighter_class_id = classes_resp.json()[0]["id"]

    resp = await client.post(
        "/characters",
        json={
            "campaign_member_id": campaign_member_id,
            "name": "Aldric",
            "race_id": human_race_id,
            "ability_scores": _STANDARD_ARRAY,
            "classes": [{"class_definition_id": fighter_class_id}],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Aldric"
    assert body["campaign_member_id"] == campaign_member_id
    assert len(body["ability_scores"]) == 6
    assert len(body["classes"]) == 1
    assert body["hit_point_max"] == 11
