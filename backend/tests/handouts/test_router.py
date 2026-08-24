"""Integration tests for the handouts HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.handouts.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.storage import get_storage_service
from tests.handouts.conftest import FakeStorageService

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


async def _make_campaign_and_invite_player(
    client: AsyncClient, dm_token: str
) -> tuple[str, str]:
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id: str = campaign_resp.json()["id"]
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
    return campaign_id, player_token


async def test_dm_uploads_handout_with_file_over_http(client: AsyncClient) -> None:
    """The DM creates a handout with a multipart file upload; gets back a URL."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id, _player_token = await _make_campaign_and_invite_player(
        client, dm_token
    )

    resp = await client.post(
        f"/campaigns/{campaign_id}/handouts",
        data={"title": "Old Map", "handout_type": "map"},
        files={"file": ("map.png", b"binary-data", "image/png")},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Old Map"
    assert body["url"] is not None
    assert body["is_revealed"] is False


async def test_player_only_sees_revealed_handouts_over_http(
    client: AsyncClient,
) -> None:
    """A player's GET list only includes handouts the DM has revealed."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id, player_token = await _make_campaign_and_invite_player(client, dm_token)

    await client.post(
        f"/campaigns/{campaign_id}/handouts",
        data={"title": "Hidden", "handout_type": "text", "content": "shh"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    reveal_resp = await client.post(
        f"/campaigns/{campaign_id}/handouts",
        data={"title": "Public", "handout_type": "text", "content": "hi"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    handout_id = reveal_resp.json()["id"]
    await client.post(
        f"/handouts/{handout_id}/reveal",
        headers={"Authorization": f"Bearer {dm_token}"},
    )

    dm_list = await client.get(
        f"/campaigns/{campaign_id}/handouts",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    player_list = await client.get(
        f"/campaigns/{campaign_id}/handouts",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert {h["title"] for h in dm_list.json()} == {"Hidden", "Public"}
    assert {h["title"] for h in player_list.json()} == {"Public"}


async def test_player_cannot_create_handout_over_http(client: AsyncClient) -> None:
    """A non-DM member is rejected (403) when creating a handout."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_id, player_token = await _make_campaign_and_invite_player(client, dm_token)

    resp = await client.post(
        f"/campaigns/{campaign_id}/handouts",
        data={"title": "Secret", "handout_type": "text", "content": "shh"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403
