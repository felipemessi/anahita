"""Integration tests for the combat WebSocket endpoint (PRD §10).

Uses Starlette's synchronous `TestClient` (not the async httpx client used by
the REST router tests) — it's what actually drives WebSocket test
connections against an ASGI app.
"""

import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.auth.models  # noqa: F401 — registers models with Base
import app.campaigns.models  # noqa: F401 — registers models with Base
import app.catalog.models  # noqa: F401 — registers models with Base
import app.characters.models  # noqa: F401 — registers models with Base
import app.combat.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def client() -> Generator[TestClient]:
    """Provide a sync TestClient wired to the FastAPI app with an isolated DB.

    Uses a plain sync fixture (not the async `db`/`client` fixtures the rest
    of the suite uses) because WebSocket testing requires Starlette's sync
    `TestClient` — it drives the ASGI app from a background thread, which is
    incompatible with pytest-asyncio's event loop for async fixtures.
    """
    engine = create_async_engine(_TEST_DB_URL, echo=False)

    async def _create_tables() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create_tables())

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_db() -> AsyncSession:  # type: ignore[misc]
        async with factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)

        async def _drop_tables() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()

        asyncio.run(_drop_tables())


def _register_and_login(client: TestClient, email: str) -> str:
    client.post(
        "/auth/register",
        json={"email": email, "username": email.split("@")[0], "password": "pass1234"},
    )
    login_resp = client.post(
        "/auth/login", json={"email": email, "password": "pass1234"}
    )
    token: str = login_resp.json()["access_token"]
    return token


def _make_campaign_session_and_encounter(client: TestClient, dm_token: str) -> str:
    campaign_resp = client.post(
        "/campaigns",
        json={"name": "Waterdeep"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    campaign_id = campaign_resp.json()["id"]
    session_resp = client.post(
        f"/campaigns/{campaign_id}/sessions",
        json={"title": "Session 1"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    session_id = session_resp.json()["id"]
    encounter_resp = client.post(
        f"/sessions/{session_id}/encounters",
        json={"name": "Ambush"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    encounter_id: str = encounter_resp.json()["id"]
    return encounter_id


def _invite_player(client: TestClient, dm_token: str) -> str:
    campaign_resp = client.get(
        "/campaigns", headers={"Authorization": f"Bearer {dm_token}"}
    )
    campaign_id = campaign_resp.json()[0]["id"]
    invite_resp = client.post(
        f"/campaigns/{campaign_id}/invites",
        json={"role": "player"},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    invite_code = invite_resp.json()["invite_code"]
    player_token = _register_and_login(client, "player@example.com")
    client.post(
        "/campaigns/invites/redeem",
        json={"invite_code": invite_code},
        headers={"Authorization": f"Bearer {player_token}"},
    )
    return player_token


def test_connect_receives_state_sync(client: TestClient) -> None:
    """On connect, the client immediately receives a full state_sync frame."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        frame = ws.receive_json()
        assert frame["event_type"] == "state_sync"
        assert frame["payload"]["id"] == encounter_id
        assert frame["payload"]["participants"] == []


def test_unauthenticated_connection_is_rejected(client: TestClient) -> None:
    """A missing/invalid token closes the connection with code 4401."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    with (
        pytest.raises(Exception),  # noqa: B017, PT011 — starlette raises WebSocketDisconnect
        client.websocket_connect(f"/ws/combat/{encounter_id}?token=garbage") as ws,
    ):
        ws.receive_json()


def test_non_member_connection_is_rejected(client: TestClient) -> None:
    """An authenticated user who isn't a campaign member is rejected (4403)."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)
    outsider_token = _register_and_login(client, "outsider@example.com")

    with (
        pytest.raises(Exception),  # noqa: B017, PT011
        client.websocket_connect(
            f"/ws/combat/{encounter_id}?token={outsider_token}"
        ) as ws,
    ):
        ws.receive_json()


def test_dm_advance_turn_broadcasts_to_all_connections(client: TestClient) -> None:
    """advance_turn from the DM reaches every connected client, DM and player alike."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)
    player_token = _invite_player(client, dm_token)

    client.post(
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

    with (
        client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as dm_ws,
        client.websocket_connect(
            f"/ws/combat/{encounter_id}?token={player_token}"
        ) as player_ws,
    ):
        dm_ws.receive_json()  # initial state_sync
        player_ws.receive_json()  # initial state_sync

        dm_ws.send_json({"event_type": "advance_turn", "payload": {}})

        dm_frame = dm_ws.receive_json()
        player_frame = player_ws.receive_json()
        assert dm_frame["event_type"] == "turn_advanced"
        assert player_frame["event_type"] == "turn_advanced"
        assert dm_frame["payload"] == player_frame["payload"]


def test_player_command_is_rejected(client: TestClient) -> None:
    """A player sending a DM-only command gets an error frame, no state change."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)
    player_token = _invite_player(client, dm_token)

    with client.websocket_connect(
        f"/ws/combat/{encounter_id}?token={player_token}"
    ) as player_ws:
        player_ws.receive_json()  # initial state_sync

        player_ws.send_json({"event_type": "advance_turn", "payload": {}})
        frame = player_ws.receive_json()
        assert frame["event_type"] == "error"

    get_resp = client.get(
        f"/encounters/{encounter_id}", headers={"Authorization": f"Bearer {dm_token}"}
    )
    assert get_resp.json()["current_round"] == 1


def test_update_participant_damage_broadcasts_participant_updated(
    client: TestClient,
) -> None:
    """update_participant (damage) broadcasts participant_updated with the new HP."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    add_resp = client.post(
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
    participant_id = add_resp.json()["participants"][0]["id"]

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json(
            {
                "event_type": "update_participant",
                "payload": {"participant_id": participant_id, "hit_point_current": 2},
            }
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "participant_updated"
        assert frame["payload"]["hit_point_current"] == 2


def test_update_participant_adds_condition(client: TestClient) -> None:
    """update_participant with add_condition attaches a condition to the participant."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    add_resp = client.post(
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
    participant_id = add_resp.json()["participants"][0]["id"]

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json(
            {
                "event_type": "update_participant",
                "payload": {"participant_id": participant_id, "add_condition": "prone"},
            }
        )
        frame = ws.receive_json()
        conditions = frame["payload"]["conditions"]
        assert len(conditions) == 1
        assert conditions[0]["condition"] == "prone"


def test_end_encounter_broadcasts_status_changed(client: TestClient) -> None:
    """end_encounter transitions status and broadcasts encounter_status_changed."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json({"event_type": "end_encounter", "payload": {}})
        frame = ws.receive_json()
        assert frame["event_type"] == "encounter_status_changed"
        assert frame["payload"]["status"] == "completed"


def test_reconnect_receives_fresh_state_sync(client: TestClient) -> None:
    """Disconnecting and reconnecting always yields a brand-new state_sync."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "event_type": "add_participant",
                "payload": {
                    "name": "Goblin",
                    "initiative": 10,
                    "hit_point_max": 7,
                    "armor_class": 15,
                    "turn_order": 0,
                },
            }
        )
        ws.receive_json()
    # connection closed here — client reconnects fresh below

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws2:
        frame = ws2.receive_json()
        assert frame["event_type"] == "state_sync"
        assert len(frame["payload"]["participants"]) == 1
        assert frame["payload"]["participants"][0]["name"] == "Goblin"


def test_player_can_roll_initiative_for_own_participant(client: TestClient) -> None:
    """A player can roll_initiative for their own participant; it broadcasts."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)
    player_token = _invite_player(client, dm_token)

    add_resp = client.post(
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
    participant_id = add_resp.json()["participants"][0]["id"]

    with (
        client.websocket_connect(
            f"/ws/combat/{encounter_id}?token={dm_token}"
        ) as dm_ws,
        client.websocket_connect(
            f"/ws/combat/{encounter_id}?token={player_token}"
        ) as player_ws,
    ):
        dm_ws.receive_json()  # initial state_sync
        player_ws.receive_json()  # initial state_sync

        # A player rolling for an NPC (not their own character) is rejected.
        player_ws.send_json(
            {
                "event_type": "roll_initiative",
                "payload": {"participant_id": participant_id, "initiative": 12},
            }
        )
        frame = player_ws.receive_json()
        assert frame["event_type"] == "error"


def test_dm_roll_initiative_broadcasts_participant_updated(client: TestClient) -> None:
    """The DM rolling initiative for an NPC broadcasts participant_updated."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    add_resp = client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    participant_id = add_resp.json()["participants"][0]["id"]

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json(
            {
                "event_type": "roll_initiative",
                "payload": {"participant_id": participant_id, "initiative": 9},
            }
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "participant_updated"
        assert frame["payload"]["initiative"] == 9


def test_dm_declare_action_manual_attack_broadcasts_action_resolved(
    client: TestClient,
) -> None:
    """declare_action with manual bonuses resolves and broadcasts action_resolved."""
    dm_token = _register_and_login(client, "dm@example.com")
    encounter_id = _make_campaign_session_and_encounter(client, dm_token)

    attacker_resp = client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Ogre",
            "hit_point_max": 30,
            "armor_class": 11,
            "turn_order": 0,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    attacker_id = attacker_resp.json()["participants"][0]["id"]
    target_resp = client.post(
        f"/encounters/{encounter_id}/participants",
        json={
            "name": "Goblin",
            "hit_point_max": 7,
            "armor_class": 15,
            "turn_order": 1,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    target_id = target_resp.json()["participants"][1]["id"]

    with client.websocket_connect(f"/ws/combat/{encounter_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json(
            {
                "event_type": "declare_action",
                "payload": {
                    "participant_id": attacker_id,
                    "target_id": target_id,
                    "action_type": "attack_weapon",
                    "manual_attack_bonus": 5,
                    "manual_damage_expression": "2d6+3",
                    "manual_attack_roll": 20,
                    "manual_damage_roll": 10,
                },
            }
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "action_resolved"
        assert frame["payload"]["hit"] is True
        assert frame["payload"]["damage_rolled"] == 10
