import { apiFetch } from "@/lib/api/client";
import type { MapToken, MapTokenCreate, SessionMap } from "@/types/map";

/**
 * Calls the maps HTTP endpoints exposed by backend/app/maps/router.py.
 * Live token movement also goes over WebSocket — see lib/ws/map-socket.ts —
 * but every mutation here broadcasts to connected sockets too (see
 * `MapService._broadcast` on the backend), so a DM using these REST calls
 * directly still updates everyone's live view.
 */

export interface UploadMapFields {
  name: string;
  width_px: number;
  height_px: number;
  grid_size_px: number;
}

/** Upload a battle map image for a session, with its grid geometry. DM only. */
export function uploadMap(
  sessionId: string,
  fields: UploadMapFields,
  file: File,
): Promise<SessionMap> {
  const form = new FormData();
  form.append("name", fields.name);
  form.append("width_px", String(fields.width_px));
  form.append("height_px", String(fields.height_px));
  form.append("grid_size_px", String(fields.grid_size_px));
  form.append("file", file);

  return apiFetch<SessionMap>(`/sessions/${sessionId}/maps`, {
    method: "POST",
    body: form,
  });
}

/** List a session's maps. Viewable by any campaign member. */
export function listMaps(sessionId: string): Promise<SessionMap[]> {
  return apiFetch<SessionMap[]>(`/sessions/${sessionId}/maps`);
}

/** Place a token (PC/NPC/monster/manual) on a map. DM only. */
export function createToken(mapId: string, data: MapTokenCreate): Promise<MapToken> {
  return apiFetch<MapToken>(`/maps/${mapId}/tokens`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * Reposition a token over REST (an alternative to the `move_token` WS
 * command — same server-side ownership/speed rule either way).
 */
export function moveToken(tokenId: string, x: number, y: number): Promise<MapToken> {
  return apiFetch<MapToken>(`/tokens/${tokenId}`, {
    method: "PATCH",
    body: JSON.stringify({ x, y }),
  });
}

/** Remove a token from a map. DM only. */
export function deleteToken(tokenId: string): Promise<void> {
  return apiFetch<void>(`/tokens/${tokenId}`, { method: "DELETE" });
}

/** Tokens within `radiusCells` of `(centerX, centerY)` — area target selection. */
export function tokensInRadius(
  mapId: string,
  centerX: number,
  centerY: number,
  radiusCells: number,
): Promise<MapToken[]> {
  const params = new URLSearchParams({
    center_x: String(centerX),
    center_y: String(centerY),
    radius_cells: String(radiusCells),
  });
  return apiFetch<MapToken[]>(`/maps/${mapId}/tokens/in-radius?${params.toString()}`);
}
