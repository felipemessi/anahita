/**
 * Message shapes for `/ws/map/{map_id}` — mirrors
 * backend/app/maps/ws_router.py and schemas.py. Envelope:
 * `{"event_type": "...", "payload": {...}}`. Kept in its own file (not
 * lib/ws/types.ts) since it's a separate socket with no shared event/command
 * union with combat's.
 */

import type { MapSnapshot, MapToken } from "@/types/map";

export interface WSErrorPayload {
  detail: string;
}

/** Server → client events. */
export type MapServerEvent =
  | { event_type: "state_sync"; payload: MapSnapshot }
  | { event_type: "token_added"; payload: MapToken }
  | { event_type: "token_moved"; payload: MapToken }
  | { event_type: "token_removed"; payload: { id: string } }
  | { event_type: "error"; payload: WSErrorPayload };

/** Payload for the `move_token` command. */
export interface WSMoveTokenPayload {
  token_id: string;
  x: number;
  y: number;
}

/** Client (any campaign member) → server commands. */
export type MapClientCommand = {
  event_type: "move_token";
  payload: WSMoveTokenPayload;
};
