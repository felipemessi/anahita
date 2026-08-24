/**
 * Mirrors backend/app/handouts/schemas.py (PRD §7.8, §10.3).
 */

export type HandoutType = "text" | "image" | "map";

export interface Handout {
  id: string;
  campaign_id: string;
  /** null when the handout is general to the campaign, not tied to one session. */
  session_id: string | null;
  title: string;
  /** Text content for `handout_type: "text"`. */
  content: string | null;
  handout_type: HandoutType;
  /** Resolved URL to the uploaded file, or null for a text handout. */
  url: string | null;
  is_revealed: boolean;
  revealed_at: string | null;
  created_at: string;
}

/** Form fields for `POST /campaigns/{id}/handouts` — sent as `multipart/form-data`. */
export interface HandoutCreateFields {
  title: string;
  handout_type: HandoutType;
  content?: string;
  session_id?: string;
}

/** Payload of the `handout_revealed` WebSocket event (PRD §10.3). */
export interface HandoutRevealedPayload {
  id: string;
  title: string;
  handout_type: HandoutType;
  url: string | null;
}
