"""Integration test for handout_revealed over the combat WebSocket (PRD §10.3)."""

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
import app.handouts.models  # noqa: F401 — registers models with Base
import app.sessions.models  # noqa: F401 — registers models with Base
from app.database import Base, get_db
from app.main import app as fastapi_app
from app.storage import get_storage_service
from tests.handouts.conftest import FakeStorageService

_TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def client() -> Generator[TestClient]:
    """Provide a sync TestClient (required for WebSocket tests) with an isolated DB."""
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


def _make_campaign_session_and_active_encounter(
    client: TestClient, dm_token: str
) -> tuple[str, str]:
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
    encounter_id = encounter_resp.json()["id"]
    client.post(
        f"/encounters/{encounter_id}/start",
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    return campaign_id, session_id


def _invite_player(client: TestClient, dm_token: str, campaign_id: str) -> str:
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


def test_reveal_broadcasts_to_connected_players(client: TestClient) -> None:
    """Revealing a handout during an active encounter reaches connected players."""
    dm_token = _register_and_login(client, "dm@example.com")
    campaign_id, session_id = _make_campaign_session_and_active_encounter(
        client, dm_token
    )
    player_token = _invite_player(client, dm_token, campaign_id)

    handout_resp = client.post(
        f"/campaigns/{campaign_id}/handouts",
        data={
            "title": "Old Map",
            "handout_type": "map",
            "session_id": session_id,
        },
        headers={"Authorization": f"Bearer {dm_token}"},
    )
    handout_id = handout_resp.json()["id"]

    encounter_id = client.get(
        f"/sessions/{session_id}/encounters",
        headers={"Authorization": f"Bearer {dm_token}"},
    ).json()[0]["id"]

    with client.websocket_connect(
        f"/ws/combat/{encounter_id}?token={player_token}"
    ) as player_ws:
        player_ws.receive_json()  # initial state_sync

        client.post(
            f"/handouts/{handout_id}/reveal",
            headers={"Authorization": f"Bearer {dm_token}"},
        )

        frame = player_ws.receive_json()
        assert frame["event_type"] == "handout_revealed"
        assert frame["payload"]["id"] == handout_id
        assert frame["payload"]["title"] == "Old Map"
