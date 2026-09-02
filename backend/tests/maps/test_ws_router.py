"""Integration tests for the maps WebSocket endpoint (backlog Fase 15 história 4).

Same `TestClient` approach as `tests/combat/test_ws_router.py` — WebSocket
testing requires Starlette's sync `TestClient`, not the async httpx client.
"""

import asyncio
import io
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
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
def client() -> Generator[TestClient]:
    """Provide a sync TestClient wired to the FastAPI app with an isolated DB."""
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
    fastapi_app.dependency_overrides[get_storage_service] = FakeStorageService
    try:
        with TestClient(fastapi_app) as test_client:
            yield test_client
    finally:
        fastapi_app.dependency_overrides.pop(get_db, None)
        fastapi_app.dependency_overrides.pop(get_storage_service, None)

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


def _make_campaign_session_and_map(client: TestClient, dm_token: str) -> str:
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
    map_resp = client.post(
        f"/sessions/{session_id}/maps",
        data={
            "name": "Tavern",
            "width_px": "1000",
            "height_px": "800",
            "grid_size_px": "50",
        },
        files={"file": ("tavern.png", io.BytesIO(b"fake-png-bytes"), "image/png")},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    map_id: str = map_resp.json()["id"]
    return map_id


def test_connect_receives_state_sync(client: TestClient) -> None:
    """On connect, the client immediately receives the map + its (empty) tokens."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)

    with client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as ws:
        frame = ws.receive_json()
        assert frame["event_type"] == "state_sync"
        assert frame["payload"]["map"]["id"] == map_id
        assert frame["payload"]["tokens"] == []


def test_unauthenticated_connection_is_rejected(client: TestClient) -> None:
    """A missing/invalid token closes the connection with code 4401."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)

    with (
        pytest.raises(Exception),  # noqa: B017, PT011
        client.websocket_connect(f"/ws/map/{map_id}?token=garbage") as ws,
    ):
        ws.receive_json()


def test_non_member_connection_is_rejected(client: TestClient) -> None:
    """An authenticated user who isn't a campaign member is rejected (4403)."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)
    outsider_token = _register_and_login(client, "outsider@example.com")

    with (
        pytest.raises(Exception),  # noqa: B017, PT011
        client.websocket_connect(f"/ws/map/{map_id}?token={outsider_token}") as ws,
    ):
        ws.receive_json()


def test_rest_token_creation_broadcasts_token_added(client: TestClient) -> None:
    """Creating a token via the plain REST endpoint still broadcasts live."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)
    player_token = _invite_player(client, dm_token)

    with (
        client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as dm_ws,
        client.websocket_connect(f"/ws/map/{map_id}?token={player_token}") as player_ws,
    ):
        dm_ws.receive_json()  # initial state_sync
        player_ws.receive_json()  # initial state_sync

        client.post(
            f"/maps/{map_id}/tokens",
            json={"name": "A Goblin", "x": 1, "y": 2},
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        dm_frame = dm_ws.receive_json()
        player_frame = player_ws.receive_json()
        assert dm_frame["event_type"] == "token_added"
        assert player_frame["event_type"] == "token_added"
        assert dm_frame["payload"]["name"] == "A Goblin"


def test_move_token_command_broadcasts_token_moved(client: TestClient) -> None:
    """The move_token WS command repositions the token and broadcasts it."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)

    token_resp = client.post(
        f"/maps/{map_id}/tokens",
        json={"name": "A Goblin", "x": 0, "y": 0},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    token_id = token_resp.json()["id"]

    with client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        ws.send_json(
            {
                "event_type": "move_token",
                "payload": {"token_id": token_id, "x": 5, "y": 5},
            }
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "token_moved"
        assert (frame["payload"]["x"], frame["payload"]["y"]) == (5, 5)


def test_delete_token_broadcasts_token_removed(client: TestClient) -> None:
    """Deleting a token via REST broadcasts token_removed to connected sockets."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)

    token_resp = client.post(
        f"/maps/{map_id}/tokens",
        json={"name": "A Goblin", "x": 0, "y": 0},
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    token_id = token_resp.json()["id"]

    with client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as ws:
        ws.receive_json()  # initial state_sync

        client.delete(
            f"/tokens/{token_id}", headers={"Authorization": f"Bearer {dm_token}"}
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "token_removed"
        assert frame["payload"]["id"] == token_id


def test_reconnect_receives_fresh_state_sync(client: TestClient) -> None:
    """Disconnecting and reconnecting always yields a brand-new state_sync."""
    dm_token = _register_and_login(client, "dm@example.com")
    map_id = _make_campaign_session_and_map(client, dm_token)

    with client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as ws:
        ws.receive_json()
        ws.send_json(
            {
                "event_type": "move_token",
                "payload": {
                    "token_id": "00000000-0000-0000-0000-000000000000",
                    "x": 1,
                    "y": 1,
                },
            }
        )
        frame = ws.receive_json()
        assert frame["event_type"] == "error"  # unknown token id

    client.post(
        f"/maps/{map_id}/tokens",
        json={"name": "A Goblin", "x": 3, "y": 3},
        headers={"Authorization": f"Bearer {dm_token}"},
    )

    with client.websocket_connect(f"/ws/map/{map_id}?token={dm_token}") as ws2:
        frame = ws2.receive_json()
        assert frame["event_type"] == "state_sync"
        assert len(frame["payload"]["tokens"]) == 1
        assert frame["payload"]["tokens"][0]["name"] == "A Goblin"
