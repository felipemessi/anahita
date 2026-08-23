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


async def test_dm_can_invite_and_player_can_redeem(client: AsyncClient) -> None:
    """The DM creates an invite over HTTP and a second user redeems it."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    invite_resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert invite_resp.status_code == 201
    invite_code = invite_resp.json()["invite_code"]

    player_token = await _register_and_login(client, "player@example.com")
    redeem_resp = await client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert redeem_resp.status_code == 200
    body = redeem_resp.json()
    assert body["campaign_id"] == campaign_id
    assert body["role"] == "player"


async def test_list_campaigns_returns_only_the_users_own(client: AsyncClient) -> None:
    """GET /campaigns filtered to the authenticated user's own campaigns."""
    alice_token = await _register_and_login(client, "alice@example.com")
    await client.post(
        "/campaigns",
        json={"name": "Alice's Table"},
        headers={"Authorization": f"Bearer {alice_token}"},
    )
    bob_token = await _register_and_login(client, "bob@example.com")
    await client.post(
        "/campaigns",
        json={"name": "Bob's Table"},
        headers={"Authorization": f"Bearer {bob_token}"},
    )

    resp = await client.get(
        "/campaigns", headers={"Authorization": f"Bearer {alice_token}"}
    )
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert names == ["Alice's Table"]


async def test_non_dm_cannot_create_invite_over_http(client: AsyncClient) -> None:
    """A non-DM member is rejected with 403 when creating an invite."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.post(
        f"/campaigns/{campaign_id}/invites",
        json={},
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 403


async def test_get_campaign_returns_detail_for_member(client: AsyncClient) -> None:
    """GET /campaigns/{id} returns the campaign detail for one of its members."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep", "setting": "Sword Coast"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    resp = await client.get(
        f"/campaigns/{campaign_id}", headers={"Authorization": f"Bearer {dm_token}"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == campaign_id
    assert body["name"] == "Waterdeep"


async def test_get_campaign_404_for_non_member(client: AsyncClient) -> None:
    """GET /campaigns/{id} is rejected for a user who isn't a member."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    outsider_token = await _register_and_login(client, "outsider@example.com")
    resp = await client.get(
        f"/campaigns/{campaign_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert resp.status_code == 404


async def test_list_members_returns_dm_and_player(client: AsyncClient) -> None:
    """GET /campaigns/{id}/members lists every member, DM and players alike."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
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

    resp = await client.get(
        f"/campaigns/{campaign_id}/members",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 200
    roles = sorted(m["role"] for m in resp.json())
    assert roles == ["dm", "player"]


async def test_update_campaign_over_http(client: AsyncClient) -> None:
    """The DM can update a campaign's general settings."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]

    resp = await client.patch(
        f"/campaigns/{campaign_id}",
        json={"description": "Updated description", "setting": "Forgotten Realms"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Waterdeep"
    assert body["description"] == "Updated description"
    assert body["setting"] == "Forgotten Realms"


async def test_update_campaign_forbidden_for_non_dm(client: AsyncClient) -> None:
    """A non-DM member cannot update the campaign's settings."""
    dm_token = await _register_and_login(client, "dm@example.com")
    campaign_resp = await client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
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

    resp = await client.patch(
        f"/campaigns/{campaign_id}",
        json={"name": "Hijacked"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403
