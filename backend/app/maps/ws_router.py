"""WebSocket endpoint for live map/token updates (backlog Fase 15 história 4).

Envelope matches combat's: `{"event_type": ..., "payload": {...}}`. Server →
clients: `state_sync` (full map + tokens, sent on every connect/reconnect),
`token_moved`, `token_added`, `token_removed` (also emitted by the plain
REST endpoints in `app.maps.router`, not just this socket — see
`MapService._broadcast`), plus `error` for a rejected command. Client → server:
`move_token` — any campaign member may send it, same ownership/speed rule as
the REST `PATCH /tokens/{id}` (`MapService.update_token_position` enforces
it either way).
"""

import uuid
from typing import Annotated, Any

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.maps.schemas import MapSnapshotRead, MapTokenRead, WSMoveTokenPayload
from app.maps.service import MapService
from app.maps.ws_manager import manager
from app.storage import get_storage_service
from app.storage.base import StorageService

router = APIRouter(tags=["maps-ws"])


async def _authenticate(token: str) -> uuid.UUID | None:
    """Resolve `token` (JWT) to a user id, or None if invalid — mirrors combat's."""
    try:
        payload = decode_token(token)
        raw_id = payload.get("sub")
        if not raw_id or not isinstance(raw_id, str):
            return None
        return uuid.UUID(raw_id)
    except (jwt.InvalidTokenError, ValueError):
        return None


@router.websocket("/ws/map/{map_id}")
async def map_ws(
    websocket: WebSocket,
    map_id: uuid.UUID,
    token: Annotated[str, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    storage: Annotated[StorageService, Depends(get_storage_service)],
) -> None:
    """Live map socket: syncs state on connect, then streams token movement."""
    await websocket.accept()

    user_id = await _authenticate(token)
    if user_id is None:
        await websocket.close(code=4401, reason="Invalid or missing token")
        return

    service = MapService(storage)
    try:
        snapshot = await service.get_snapshot(map_id, user_id, db)
    except HTTPException:
        await websocket.close(code=4403, reason="Not a member of this campaign")
        return

    manager.connect(map_id, websocket)
    try:
        await websocket.send_json(_envelope("state_sync", snapshot))
        while True:
            message = await websocket.receive_json()
            await _handle_message(message, map_id, user_id, service, db, websocket)
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(map_id, websocket)


def _envelope(
    event_type: str, model: MapSnapshotRead | MapTokenRead | Any
) -> dict[str, Any]:
    """Build a `{"event_type": ..., "payload": ...}` frame from a schema or dict."""
    if isinstance(model, MapSnapshotRead | MapTokenRead):
        payload = model.model_dump(mode="json")
    else:
        payload = model
    return {"event_type": event_type, "payload": payload}


async def _handle_message(
    message: dict[str, Any],
    map_id: uuid.UUID,
    user_id: uuid.UUID,
    service: MapService,
    db: AsyncSession,
    websocket: WebSocket,
) -> None:
    """Dispatch one incoming command, or send an `error` frame if rejected.

    `service.update_token_position` already broadcasts `token_moved` to
    every connected socket (including this one) via `MapService._broadcast`
    — this handler doesn't broadcast a second time.
    """
    event_type = message.get("event_type")
    payload = message.get("payload") or {}

    if event_type != "move_token":
        await websocket.send_json(
            _envelope("error", {"detail": f"Unknown event_type '{event_type}'"})
        )
        return

    try:
        move_data = WSMoveTokenPayload.model_validate(payload)
        await service.update_token_position(
            move_data.token_id, user_id, move_data.x, move_data.y, db
        )
    except ValidationError as exc:
        await websocket.send_json(_envelope("error", {"detail": str(exc)}))
    except HTTPException as exc:
        await websocket.send_json(_envelope("error", {"detail": exc.detail}))
