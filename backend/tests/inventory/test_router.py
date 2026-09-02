"""Integration tests for the inventory HTTP endpoints."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.inventory.models  # noqa: F401 — registers models with Base
import app.maps.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.catalog.models import EquipmentCategory
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

    # Homebrew item creation resolves `item_type` to an SRD equipment
    # category index (`app.catalog.service.create_custom_item`) — seed just
    # the "weapon" one these tests need, instead of the full SRD catalog.
    async with factory() as seed_session:
        seed_session.add(EquipmentCategory(index="weapon", is_custom=False))
        await seed_session.commit()

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


async def _make_campaign_encounter_and_player(
    client: AsyncClient, dm_token: str
) -> tuple[str, str, str]:
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
    session_id = session_resp.json()["id"]
    encounter_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = encounter_resp.json()["id"]

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
    return campaign_id, encounter_id, player_token


async def _create_homebrew_item(
    client: AsyncClient, dm_token: str, campaign_id: str
) -> str:
    resp = await client.post(
        "/catalog/items",
        json={
            "campaign_id": campaign_id,
            "name": "Rusty Dagger",
            "item_type": "weapon",
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    item_id: str = resp.json()["id"]
    return item_id


async def test_dm_adds_item_player_lists_it_over_http(client: AsyncClient) -> None:
    """The DM adds an item to the party inventory; the player can list it."""
    dm_token = await _register_and_login(client, "dm@example.com")
    (
        campaign_id,
        _encounter_id,
        player_token,
    ) = await _make_campaign_encounter_and_player(client, dm_token)
    item_id = await _create_homebrew_item(client, dm_token, campaign_id)

    add_resp = await client.post(
        f"/campaigns/{campaign_id}/inventory",
        json={"item_id": item_id, "quantity": 2},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert add_resp.status_code == 201

    list_resp = await client.get(
        f"/campaigns/{campaign_id}/inventory",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1
    assert list_resp.json()[0]["quantity"] == 2


async def test_player_cannot_add_inventory_over_http(client: AsyncClient) -> None:
    """A non-DM member is rejected (403) when adding to the party inventory."""
    dm_token = await _register_and_login(client, "dm@example.com")
    (
        campaign_id,
        _encounter_id,
        player_token,
    ) = await _make_campaign_encounter_and_player(client, dm_token)
    item_id = await _create_homebrew_item(client, dm_token, campaign_id)

    resp = await client.post(
        f"/campaigns/{campaign_id}/inventory",
        json={"item_id": item_id, "quantity": 1},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


async def test_dm_distributes_custom_and_currency_loot_over_http(
    client: AsyncClient,
) -> None:
    """The DM records both a custom-item drop and a pure-currency drop."""
    dm_token = await _register_and_login(client, "dm@example.com")
    (
        campaign_id,
        encounter_id,
        _player_token,
    ) = await _make_campaign_encounter_and_player(client, dm_token)

    custom_resp = await client.post(
        f"/encounters/{encounter_id}/loot",
        json={"custom_item_name": "Shiny Gem", "quantity": 1},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert custom_resp.status_code == 201
    assert custom_resp.json()["custom_item_name"] == "Shiny Gem"

    currency_resp = await client.post(
        f"/encounters/{encounter_id}/loot",
        json={"currency_cp": 500},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert currency_resp.status_code == 201
    assert currency_resp.json()["currency_cp"] == 500

    list_resp = await client.get(
        f"/encounters/{encounter_id}/loot",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert len(list_resp.json()) == 2


async def test_loot_drop_with_conflicting_item_fields_is_rejected_over_http(
    client: AsyncClient,
) -> None:
    """A loot drop naming both a catalog item and a custom name 422s."""
    dm_token = await _register_and_login(client, "dm@example.com")
    (
        campaign_id,
        encounter_id,
        _player_token,
    ) = await _make_campaign_encounter_and_player(client, dm_token)
    item_id = await _create_homebrew_item(client, dm_token, campaign_id)

    resp = await client.post(
        f"/encounters/{encounter_id}/loot",
        json={"item_id": item_id, "custom_item_name": "Shiny Gem"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert resp.status_code == 422
