/**
 * Mirrors backend/app/journal/schemas.py (Fase 5 do backend — Registro e
 * Lore, PRD §7.10). Every entry is DM-only, never visible to players.
 */

export interface JournalEntry {
  id: string;
  campaign_id: string;
  author_id: string;
  title: string;
  content: string;
  session_id: string | null;
  created_at: string;
}

export interface JournalEntryCreate {
  title: string;
  content?: string;
  session_id?: string | null;
}

export interface JournalEntryUpdate {
  title?: string;
  content?: string;
  session_id?: string | null;
}
