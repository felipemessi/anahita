import { apiFetch } from "@/lib/api/client";
import type {
  GameSession,
  SessionCreate,
  SessionNote,
  SessionNoteCreate,
} from "@/types/session";

/** Calls the sessions endpoints exposed by backend/app/sessions/router.py. */

/** List a campaign's sessions, in order; `dm_notes` is only populated for the DM. */
export function listSessions(campaignId: string): Promise<GameSession[]> {
  return apiFetch<GameSession[]>(`/campaigns/${campaignId}/sessions`);
}

/** Create a session for a campaign; only the campaign's DM may do this. */
export function createSession(
  campaignId: string,
  data: SessionCreate,
): Promise<GameSession> {
  return apiFetch<GameSession>(`/campaigns/${campaignId}/sessions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List a session's notes; the DM sees private notes, other members don't. */
export function listNotes(sessionId: string): Promise<SessionNote[]> {
  return apiFetch<SessionNote[]>(`/sessions/${sessionId}/notes`);
}

/** Add a note to a session; only the DM may mark a note private. */
export function addNote(
  sessionId: string,
  data: SessionNoteCreate,
): Promise<SessionNote> {
  return apiFetch<SessionNote>(`/sessions/${sessionId}/notes`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Open a planned session for play; only the campaign's DM may do this. */
export function openSession(sessionId: string): Promise<GameSession> {
  return apiFetch<GameSession>(`/sessions/${sessionId}/open`, { method: "POST" });
}
