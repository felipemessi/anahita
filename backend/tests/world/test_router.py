"""Integration tests for the world-building HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.world.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
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


async def test_dm_creates_npc_and_player_can_list_it(client: AsyncClient) -> None:
    """Full flow: DM creates and reveals an NPC; a fellow member can list it."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    npc_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Innkeeper Tom", "race": "Human", "description": "Runs the inn"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert npc_resp.status_code == 201
    npc_id = npc_resp.json()["id"]
    await client.post(
        f"/npcs/{npc_id}/reveal",
        headers={"Authorization": f"Bearer {dm_token}"},
    )

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

    player_npcs_resp = await client.get(
        f"/campaigns/{campaign_id}/npcs",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert len(player_npcs_resp.json()) == 1

    player_create_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Sneaky", "race": "Human", "description": ""},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_create_resp.status_code == 403


async def test_player_only_sees_revealed_npcs_over_http(client: AsyncClient) -> None:
    """A player's GET list/detail only include NPCs the DM has revealed."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    hidden_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Hidden NPC", "race": "Human", "description": ""},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    hidden_id = hidden_resp.json()["id"]
    public_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Public NPC", "race": "Human", "description": ""},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    public_id = public_resp.json()["id"]
    reveal_resp = await client.post(
        f"/npcs/{public_id}/reveal",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert reveal_resp.status_code == 200
    assert reveal_resp.json()["is_revealed"] is True

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

    dm_list = await client.get(
        f"/campaigns/{campaign_id}/npcs",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    player_list = await client.get(
        f"/campaigns/{campaign_id}/npcs",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert {n["name"] for n in dm_list.json()} == {"Hidden NPC", "Public NPC"}
    assert {n["name"] for n in player_list.json()} == {"Public NPC"}

    player_hidden_detail = await client.get(
        f"/npcs/{hidden_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_hidden_detail.status_code == 404

    player_public_detail = await client.get(
        f"/npcs/{public_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_public_detail.status_code == 200

    player_reveal_resp = await client.post(
        f"/npcs/{hidden_id}/reveal",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_reveal_resp.status_code == 403


async def test_dm_links_npc_to_faction(client: AsyncClient) -> None:
    """Full flow: DM creates an NPC and a faction, then links them."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    npc_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Volo", "race": "Human", "description": ""},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    npc_id = npc_resp.json()["id"]
    faction_resp = await client.post(
        f"/campaigns/{campaign_id}/factions",
        json={"name": "Harpers", "description": ""},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    faction_id = faction_resp.json()["id"]

    link_resp = await client.post(
        f"/npcs/{npc_id}/factions",
        json={"faction_id": faction_id, "role_in_faction": "Spymaster"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert link_resp.status_code == 201

    list_resp = await client.get(
        f"/npcs/{npc_id}/factions",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["role_in_faction"] == "Spymaster"
