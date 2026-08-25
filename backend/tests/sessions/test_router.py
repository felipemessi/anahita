"""Integration tests for the sessions HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
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


async def test_dm_creates_session_and_private_note_hidden_from_player(
    client: AsyncClient,
) -> None:
    """Full flow: DM creates a session and a private note; a player can't see it."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    session_resp = await client.post(
        f"/campaigns/{campaign_id}/sessions",
        json={"title": "Session One", "dm_notes": "secret"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert session_resp.status_code == 201
    session_body = session_resp.json()
    assert session_body["session_number"] == 1
    assert session_body["dm_notes"] == "secret"
    session_id = session_body["id"]

    private_note_resp = await client.post(
        f"/sessions/{session_id}/notes",
        json={"content": "the twist", "is_private": True},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert private_note_resp.status_code == 201

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

    player_sessions_resp = await client.get(
        f"/campaigns/{campaign_id}/sessions",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_sessions_resp.json()[0]["dm_notes"] is None

    player_notes_resp = await client.get(
        f"/sessions/{session_id}/notes",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert player_notes_resp.json() == []

    dm_notes_resp = await client.get(
        f"/sessions/{session_id}/notes",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert len(dm_notes_resp.json()) == 1


async def test_dm_opens_session_over_http(client: AsyncClient) -> None:
    """The DM can open a planned session for play over HTTP."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    session_resp = await client.post(
        f"/campaigns/{campaign_id}/sessions",
        json={"title": "Session One"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    session_id = session_resp.json()["id"]

    open_resp = await client.post(
        f"/sessions/{session_id}/open",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert open_resp.status_code == 200
    assert open_resp.json()["status"] == "in_progress"


async def test_player_cannot_open_session_over_http(client: AsyncClient) -> None:
    """A player cannot open a session over HTTP."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Icewind Dale"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    session_resp = await client.post(
        f"/campaigns/{campaign_id}/sessions",
        json={"title": "Session One"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    session_id = session_resp.json()["id"]

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

    open_resp = await client.post(
        f"/sessions/{session_id}/open",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert open_resp.status_code == 403
