import { apiFetch } from "@/lib/api/client";
import type { Encounter, EncounterCreate } from "@/types/combat";

/**
 * Calls the combat HTTP endpoints exposed by backend/app/combat/router.py.
 * Live turn-flow actions (advance turn, damage/heal, add/remove participant
 * in-session) go over WebSocket instead — see lib/ws/combat-socket.ts.
 */

/** Create an encounter for a session; only the campaign's DM may do this. */
export function createEncounter(
  sessionId: string,
  data: EncounterCreate,
): Promise<Encounter> {
  return apiFetch<Encounter>(`/sessions/${sessionId}/encounters`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List a session's encounters. Viewable by any campaign member. */
export function listEncounters(sessionId: string): Promise<Encounter[]> {
  return apiFetch<Encounter[]>(`/sessions/${sessionId}/encounters`);
}

/** Start a preparing encounter (transitions to `active`). DM only. */
export function startEncounter(encounterId: string): Promise<Encounter> {
  return apiFetch<Encounter>(`/encounters/${encounterId}/start`, {
    method: "POST",
  });
}
