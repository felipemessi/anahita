"""Integration tests for catalog homebrew-creation HTTP endpoints."""

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


async def _register_and_login(client: AsyncClient, email: str) -> str:
    await client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "pass1234"},
    )
    login_resp = await client.post(
        "/auth/login", json={"email": email, "password": "pass1234"}
    )
    token: str = login_resp.json()["access_token"]
    return token


async def _make_campaign(client: AsyncClient, dm_token: str, name: str) -> str:
    resp = await client.post(
        "/campaigns",
        json={"name": name},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id: str = resp.json()["id"]
    return campaign_id


async def test_create_race_requires_dm(client: AsyncClient) -> None:
    """A non-DM member is rejected with 403 when creating homebrew."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    resp = await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_id, "name": "Homebrew Elf"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


async def test_create_race_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew race scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/races",
        json={
            "campaign_id": campaign_id,
            "name": "Duskling",
            "description": "A twilight-touched folk.",
            "speed": 25,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Duskling"
    assert body["speed"] == 25
    assert body["is_custom"] is True


async def test_created_homebrew_visible_only_in_own_campaign(
    client: AsyncClient,
) -> None:
    """`GET /catalog/races?campaign_id=` scopes homebrew to that campaign only."""
    dm_a_token = await _register_and_login(client, "dm-a@example.com")
    campaign_a = await _make_campaign(client, dm_a_token, "Campaign A")
    dm_b_token = await _register_and_login(client, "dm-b@example.com")
    campaign_b = await _make_campaign(client, dm_b_token, "Campaign B")

    await client.post(
        "/catalog/races",
        json={"campaign_id": campaign_a, "name": "Campaign A Homebrew"},
        headers={"Authorization": f"Bearer {dm_a_token}"},
    )

    resp = await client.get(
        "/catalog/races",
        params={"campaign_id": campaign_b, "include_custom": True},
    )
    names = [r["name"] for r in resp.json()]
    assert "Campaign A Homebrew" not in names

    own_resp = await client.get(
        "/catalog/races",
        params={"campaign_id": campaign_a, "include_custom": True},
    )
    own_names = [r["name"] for r in own_resp.json()]
    assert "Campaign A Homebrew" in own_names


async def test_create_spell_rejects_unknown_school(client: AsyncClient) -> None:
    """Creating a homebrew spell with an unknown magic school is rejected."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/spells",
        json={
            "campaign_id": campaign_id,
            "name": "Bogus Bolt",
            "level": 1,
            "school": "not-a-real-school",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 422


async def test_create_spell_and_monster_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew spell and monster scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    spell_resp = await client.post(
        "/catalog/spells",
        json={
            "campaign_id": campaign_id,
            "name": "Homebrew Bolt",
            "level": 1,
            "school": "evocation",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert spell_resp.status_code == 201
    assert spell_resp.json()["school"] == "evocation"

    monster_resp = await client.post(
        "/catalog/monsters",
        json={
            "campaign_id": campaign_id,
            "name": "Swamp Horror",
            "size": "large",
            "creature_type": "monstrosity",
            "hit_points": 45,
            "challenge_rating": 3,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert monster_resp.status_code == 201
    assert monster_resp.json()["hit_points"] == 45


async def test_create_item_over_http(client: AsyncClient) -> None:
    """The DM can create a homebrew item scoped to their campaign."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id = await _make_campaign(client, dm_token, "Waterdeep")

    resp = await client.post(
        "/catalog/items",
        json={
            "campaign_id": campaign_id,
            "name": "Rusty Dagger",
            "item_type": "weapon",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["item_type"] == "weapon"
