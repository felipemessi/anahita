"""Integration tests for the maps HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.maps.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.storage import get_storage_service
from tests.maps.conftest import FakeStorageService

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Provide an httpx client wired to the FastAPI app with an isolated DB/storage."""
    engine = create_async_engine(_TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncGenerator[AsyncSession]:
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    fastapi_app.dependency_overrides[get_storage_service] = FakeStorageService
    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="https://test") as ac:
            yield ac
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        fastapi_app.dependency_overrides.pop(get_storage_service, None)
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


async def _make_campaign_and_session(client: AsyncClient, dm_token: str) -> str:
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    session_resp = await client.post(
        f"/campaigns/{campaign_id}/sessions",
        json={"title": "Session 1"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    session_id: str = session_resp.json()["id"]
    return session_id


async def _invite_player(client: AsyncClient, dm_token: str) -> str:
    campaign_resp = await client.get(
        "/campaigns", headers={"Authorization": f"Bearer {dm_token}"}
    )
    campaign_id = campaign_resp.json()[0]["id"]
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
    return player_token


async def test_dm_uploads_map(client: AsyncClient) -> None:
    """The DM uploads a map with a file; gets back a resolved URL."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    resp = await client.post(
        f"/sessions/{session_id}/maps",
        data={
            "name": "Tavern",
            "width_px": "1000",
            "height_px": "800",
            "grid_size_px": "50",
        },
        files={"file": ("tavern.png", b"binary-data", "image/png")},
        headers={"Authorization": f"Bearer {dm_token}"},
    )

    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Tavern"
    assert body["url"] is not None


async def test_player_cannot_upload_map(client: AsyncClient) -> None:
    """A player uploading a map gets a 403."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)
    player_token = await _invite_player(client, dm_token)

    resp = await client.post(
        f"/sessions/{session_id}/maps",
        data={
            "name": "Tavern",
            "width_px": "1000",
            "height_px": "800",
            "grid_size_px": "50",
        },
        files={"file": ("tavern.png", b"binary-data", "image/png")},
        headers={"Authorization": f"Bearer {player_token}"},
    )

    assert resp.status_code == 403


async def test_list_maps_visible_to_any_member(client: AsyncClient) -> None:
    """Any campaign member can list a session's maps."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)
    player_token = await _invite_player(client, dm_token)
    await client.post(
        f"/sessions/{session_id}/maps",
        data={
            "name": "Tavern",
            "width_px": "1000",
            "height_px": "800",
            "grid_size_px": "50",
        },
        files={"file": ("tavern.png", b"binary-data", "image/png")},
        headers={"Authorization": f"Bearer {dm_token}"},
    )

    resp = await client.get(
        f"/sessions/{session_id}/maps",
        headers={"Authorization": f"Bearer {player_token}"},
    )

    assert resp.status_code == 200
    assert len(resp.json()) == 1
