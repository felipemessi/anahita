"""WebSocket connection tracking for live combat encounters (PRD §10.1)."""

import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket


class WSConnectionManager:
    """Tracks active combat WebSocket connections, keyed by encounter.

    Fault tolerance follows PRD §10.5: Postgres is the source of truth, not
    this in-memory registry. A dropped connection loses nothing but its
    broadcast subscription — the client reconnects and gets a fresh
    `state_sync`.
    """

    def __init__(self) -> None:
        """Start with an empty connection registry."""
        self._connections: dict[uuid.UUID, list[WebSocket]] = defaultdict(list)

    def connect(self, encounter_id: uuid.UUID, websocket: WebSocket) -> None:
        """Register a connected socket as subscribed to `encounter_id`."""
        self._connections[encounter_id].append(websocket)

    def disconnect(self, encounter_id: uuid.UUID, websocket: WebSocket) -> None:
        """Unregister a socket, dropping the encounter's entry once empty."""
        connections = self._connections.get(encounter_id)
        if not connections:
            return
        if websocket in connections:
            connections.remove(websocket)
        if not connections:
            self._connections.pop(encounter_id, None)

    async def broadcast(self, encounter_id: uuid.UUID, message: dict[str, Any]) -> None:
        """Send `message` to every socket subscribed to `encounter_id`."""
        for websocket in list(self._connections.get(encounter_id, [])):
            await websocket.send_json(message)

    def connection_count(self, encounter_id: uuid.UUID) -> int:
        """Return how many sockets are currently subscribed to `encounter_id`."""
        return len(self._connections.get(encounter_id, []))


#: Module-level singleton — one connection registry per process, shared by
#: every WebSocket handled by `app.combat.ws_router`.
manager = WSConnectionManager()
