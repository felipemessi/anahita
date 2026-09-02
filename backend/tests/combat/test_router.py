"""Integration tests for the combat HTTP endpoints."""

import uuid
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


async def test_create_and_start_encounter_over_http(client: AsyncClient) -> None:
    """The DM creates an encounter, adds a participant, and starts combat."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Goblin Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert create_resp.status_code == 201
    encounter_id = create_resp.json()["id"]
    assert create_resp.json()["status"] == "preparing"

    participant_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "initiative": 14,
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert participant_resp.status_code == 200
    participants = participant_resp.json()["participants"]
    assert len(participants) == 1
    assert participants[0]["hit_point_current"] == 7

    start_resp = await client.post(
        f"/encounters/{encounter_id}/start",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert start_resp.status_code == 200
    assert start_resp.json()["status"] == "active"


async def test_non_dm_cannot_create_encounter_over_http(client: AsyncClient) -> None:
    """A non-DM member is rejected with 403 when creating an encounter."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

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

    resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert resp.status_code == 403


async def test_player_can_view_but_not_manage_encounter(client: AsyncClient) -> None:
    """A player can GET an encounter but cannot add participants to it."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

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

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = create_resp.json()["id"]

    get_resp = await client.get(
        f"/encounters/{encounter_id}",
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert get_resp.status_code == 200

    add_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "initiative": 10,
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {player_token}"},
    )
    assert add_resp.status_code == 403


async def test_add_character_participant_over_http(client: AsyncClient) -> None:
    """The DM can add a character (PC) participant, not just a monster/NPC.

    A character need not already exist for the FK to resolve in this SQLite
    test DB (see `tests.combat.conftest.campaign_with_pc`'s note on FK
    enforcement) — this exercises the same request shape the frontend's
    future `CharacterPicker` would send.
    """
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = create_resp.json()["id"]

    character_id = str(uuid.uuid4())
    participant_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "character_id": character_id,
            "name": "Aldric",
            "initiative": 15,
            "hit_point_max": 10,
            "armor_class": 14,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert participant_resp.status_code == 200
    participants = participant_resp.json()["participants"]
    assert len(participants) == 1
    assert participants[0]["character_id"] == character_id
    assert participants[0]["name"] == "Aldric"


async def test_add_character_participant_rejects_duplicate_over_http(
    client: AsyncClient,
) -> None:
    """Adding the same character twice to an encounter is rejected."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = create_resp.json()["id"]

    character_id = str(uuid.uuid4())
    body = {
        "character_id": character_id,
        "name": "Aldric",
        "initiative": 15,
        "hit_point_max": 10,
        "armor_class": 14,
        "turn_order": 0,
    }
    first_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json=body,
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert first_resp.status_code == 200

    second_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json={**body, "turn_order": 1},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert second_resp.status_code == 422


async def test_remove_participant_over_http(client: AsyncClient) -> None:
    """The DM can remove a participant from an encounter."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = create_resp.json()["id"]

    participant_resp = await client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "initiative": 10,
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    participant_id = participant_resp.json()["participants"][0]["id"]

    delete_resp = await client.delete(
        f"/encounters/{encounter_id}/participants/{participant_id}",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert delete_resp.status_code == 200
    assert delete_resp.json()["participants"] == []


async def test_get_log_over_http(client: AsyncClient) -> None:
    """GET /encounters/{id}/log returns the recorded actions in order."""
    dm_token = await _register_and_login(client, "dm@example.com")
    session_id = await _make_campaign_and_session(client, dm_token)

    create_resp = await client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id = create_resp.json()["id"]

    await client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "initiative": 10,
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )

    log_resp = await client.get(
        f"/encounters/{encounter_id}/log",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    assert log_resp.status_code == 200
    entries = log_resp.json()
    assert len(entries) == 1
    assert entries[0]["description"] == "Goblin joined the encounter"
