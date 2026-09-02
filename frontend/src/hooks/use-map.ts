"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createToken,
  deleteToken,
  listMaps,
  tokensInRadius,
  uploadMap,
  type UploadMapFields,
} from "@/lib/api/maps";
import { useMapContext } from "@/providers/map-provider";
import type { MapTokenCreate } from "@/types/map";

export const MAPS_QUERY_KEY = ["maps"] as const;

/** A session's maps. Viewable by any campaign member. */
export function useMaps(sessionId: string) {
  return useQuery({
    queryKey: [...MAPS_QUERY_KEY, sessionId],
    queryFn: () => listMaps(sessionId),
    enabled: Boolean(sessionId),
  });
}

/** Upload a battle map image for a session, with its grid geometry (DM only). */
export function useUploadMap(sessionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ fields, file }: { fields: UploadMapFields; file: File }) =>
      uploadMap(sessionId, fields, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...MAPS_QUERY_KEY, sessionId] });
    },
  });
}

/** Place a token on a map (DM only) — invalidates the map's REST-cached data. */
export function useCreateToken(mapId: string) {
  return useMutation({
    mutationFn: (data: MapTokenCreate) => createToken(mapId, data),
  });
}

/** Remove a token from a map (DM only). */
export function useDeleteToken() {
  return useMutation({
    mutationFn: (tokenId: string) => deleteToken(tokenId),
  });
}

/** Tokens within `radiusCells` of a cell — area target selection (Fase 15 história 5). */
export function useTokensInRadius() {
  return useMutation({
    mutationFn: ({
      mapId,
      centerX,
      centerY,
      radiusCells,
    }: {
      mapId: string;
      centerX: number;
      centerY: number;
      radiusCells: number;
    }) => tokensInRadius(mapId, centerX, centerY, radiusCells),
  });
}

/**
 * The current map/tokens (kept in sync by `MapProvider` over the WebSocket)
 * plus the `move_token` command sender — mirrors `useCombat`. Token
 * creation/deletion stay on the REST hooks above (mirrors the backend split:
 * the WS command only covers movement).
 */
export function useMap() {
  const { map, tokens, lastError, isConnected, sendCommand } = useMapContext();

  /**
   * Move a token — sent over WS for real-time feedback. Same
   * ownership/speed rule as the REST `PATCH /tokens/{id}` either way
   * (`MapService.update_token_position` is the single source of truth); a
   * rejected move surfaces as an `error` event (`lastError`) rather than a
   * thrown promise, so a drag-and-drop UI doesn't need to await anything.
   */
  function moveToken(tokenId: string, x: number, y: number): void {
    sendCommand({ event_type: "move_token", payload: { token_id: tokenId, x, y } });
  }

  return { map, tokens, lastError, isConnected, moveToken };
}
