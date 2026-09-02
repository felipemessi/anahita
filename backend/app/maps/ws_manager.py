"""WebSocket connection tracking for live map/token updates (backlog Fase 15).

A separate registry from `app.combat.ws_manager` (keyed by map, not
encounter) — a map can be live-updated (DM repositioning tokens while
planning) even with no active encounter, so it can't simply reuse the
combat socket's per-encounter registry. Same class shape and fault-
tolerance story as combat's: Postgres is the source of truth, a dropped
connection just loses its broadcast subscription until it reconnects and
gets a fresh `state_sync`.
"""

from app.combat.ws_manager import WSConnectionManager

#: Module-level singleton — one connection registry per process, shared by
#: every WebSocket handled by `app.maps.ws_router`. Reuses
#: `WSConnectionManager` (keyed by a UUID — here a map id instead of an
#: encounter id, the class doesn't care which) rather than duplicating its
#: logic.
manager = WSConnectionManager()
