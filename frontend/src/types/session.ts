/**
 * Mirrors backend/app/sessions/schemas.py and domain.py.
 * Keep in sync manually — no codegen yet (PRD frontend backlog Fase 0).
 */

export type SessionStatus = "planned" | "in_progress" | "completed";

export interface GameSession {
  id: string;
  campaign_id: string;
  session_number: number;
  title: string;
  scheduled_date: string | null;
  status: SessionStatus;
  /** Only populated for the campaign's DM — null for players regardless of content (PRD §7.5). */
  dm_notes: string | null;
  summary: string | null;
  created_at: string;
}

export interface SessionCreate {
  title: string;
  scheduled_date?: string | null;
  summary?: string | null;
  dm_notes?: string | null;
}

export interface SessionNote {
  id: string;
  session_id: string;
  author_id: string;
  content: string;
  is_private: boolean;
  created_at: string;
}

export interface SessionNoteCreate {
  content: string;
  is_private?: boolean;
}
