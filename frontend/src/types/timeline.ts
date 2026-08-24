/**
 * Mirrors backend/app/timeline/schemas.py (Fase 5 do backend — Registro e
 * Lore, PRD §7.10). Reads return a fused list of automatic (session) and
 * manual entries; only manual entries can be created/edited/deleted.
 */

export type TimelineEntryType = "session" | "event";

/** One fused entry — automatic (from a session's summary) or manual. */
export interface TimelineEntry {
  entry_type: TimelineEntryType;
  id: string;
  title: string;
  description: string | null;
  session_id: string | null;
  in_game_date: string | null;
  sort_order: number;
  created_at: string;
}

export interface TimelineEvent {
  id: string;
  campaign_id: string;
  title: string;
  description: string | null;
  session_id: string | null;
  in_game_date: string | null;
  sort_order: number;
  created_at: string;
}

export interface TimelineEventCreate {
  title: string;
  description?: string | null;
  session_id?: string | null;
  in_game_date?: string | null;
  sort_order: number;
}

export interface TimelineEventUpdate {
  title?: string;
  description?: string | null;
  session_id?: string | null;
  in_game_date?: string | null;
  sort_order?: number;
}
