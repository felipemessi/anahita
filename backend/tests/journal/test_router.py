"""Integration tests for the journal HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.journal.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
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


async def _setup_campaign_with_player(
    client: AsyncClient,
) -> tuple[str, str, str]:
    """Register a DM and a player, create a campaign, add the player.

    Returns (dm_token, player_token, campaign_id).
    """
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

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
    return dm_token, player_token, campaign_id


async def test_dm_creates_lists_updates_and_deletes_entry(
    client: AsyncClient,
) -> None:
    """Full flow: DM creates, lists, updates, then deletes a journal entry."""
    dm_token, _player_token, campaign_id = await _setup_campaign_with_player(client)

    create_resp = await client.post(
        f"/campaigns/{campaign_id}/journal",
        json={"title": "Session 1 aftermath", "content": "The party regroups."},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert create_resp.status_code == 201
    entry_id = create_resp.json()["id"]

    list_resp = await client.get(
        f"/campaigns/{campaign_id}/journal",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["title"] == "Session 1 aftermath"

    update_resp = await client.patch(
        f"/journal/{entry_id}",
        json={"content": "The party regroups and plans their next move."},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["content"] == "The party regroups and plans their next move."
    assert updated["title"] == "Session 1 aftermath"

    delete_resp = await client.delete(
        f"/journal/{entry_id}",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert delete_resp.status_code == 204

    list_after_delete = await client.get(
        f"/campaigns/{campaign_id}/journal",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert list_after_delete.json() == []


async def test_player_gets_403_on_every_journal_route(client: AsyncClient) -> None:
    """A player (non-DM member) is rejected on every journal endpoint."""
    dm_token, player_token, campaign_id = await _setup_campaign_with_player(client)

    create_resp = await client.post(
        f"/campaigns/{campaign_id}/journal",
        json={"title": "Secret plans", "content": "The BBEG's true identity."},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    entry_id = create_resp.json()["id"]

    player_headers = {"Authorization": f"Bearer {player_token}"}

    player_create = await client.post(
        f"/campaigns/{campaign_id}/journal",
        json={"title": "Peeking", "content": "..."},
        headers=player_headers,
    )
    assert player_create.status_code == 403

    player_list = await client.get(
        f"/campaigns/{campaign_id}/journal", headers=player_headers
    )
    assert player_list.status_code == 403

    player_update = await client.patch(
        f"/journal/{entry_id}", json={"title": "Hacked"}, headers=player_headers
    )
    assert player_update.status_code == 403

    player_delete = await client.delete(
        f"/journal/{entry_id}", headers=player_headers
    )
    assert player_delete.status_code == 403
