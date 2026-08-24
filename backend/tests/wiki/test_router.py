"""Integration tests for the wiki HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.wiki.models  # noqa: F401 — registers models with Base
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


async def test_dm_creates_page_and_links_it_player_reads_but_cannot_write(
    client: AsyncClient,
) -> None:
    """DM creates a page and links it to an NPC; a player can read, not write."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    dm_headers = {"Authorization": f"Bearer {dm_token}"}

    page_resp = await client.post(
        f"/campaigns/{campaign_id}/wiki",
        json={"title": "The Sunken Temple", "content": "Deep beneath the lake..."},
        headers=dm_headers,
    )
    assert page_resp.status_code == 201
    page_body = page_resp.json()
    assert page_body["slug"] == "the-sunken-temple"
    assert page_body["links"] == []
    page_id = page_body["id"]

    npc_resp = await client.post(
        f"/campaigns/{campaign_id}/npcs",
        json={"name": "Temple Guardian", "race": "Construct", "description": ""},
        headers=dm_headers,
    )
    npc_id = npc_resp.json()["id"]

    link_resp = await client.post(
        f"/wiki/{page_id}/links",
        json={"npc_id": npc_id},
        headers=dm_headers,
    )
    assert link_resp.status_code == 201
    link_id = link_resp.json()["id"]

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers=dm_headers,
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = await _register_and_login(client, "player@example.com")
    await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    player_headers = {"Authorization": f"Bearer {player_token}"}

    player_list = await client.get(
        f"/campaigns/{campaign_id}/wiki", headers=player_headers
    )
    assert player_list.status_code == 200
    assert len(player_list.json()) == 1

    player_get = await client.get(f"/wiki/{page_id}", headers=player_headers)
    assert player_get.status_code == 200
    assert player_get.json()["links"][0]["npc_id"] == npc_id

    player_create = await client.post(
        f"/campaigns/{campaign_id}/wiki",
        json={"title": "Fake"},
        headers=player_headers,
    )
    assert player_create.status_code == 403

    player_update = await client.patch(
        f"/wiki/{page_id}", json={"title": "Hacked"}, headers=player_headers
    )
    assert player_update.status_code == 403

    player_delete_link = await client.delete(
        f"/wiki/{page_id}/links/{link_id}", headers=player_headers
    )
    assert player_delete_link.status_code == 403

    player_delete = await client.delete(f"/wiki/{page_id}", headers=player_headers)
    assert player_delete.status_code == 403

    dm_delete_link = await client.delete(
        f"/wiki/{page_id}/links/{link_id}", headers=dm_headers
    )
    assert dm_delete_link.status_code == 204
