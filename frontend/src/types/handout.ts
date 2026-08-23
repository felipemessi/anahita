/**
 * PROVISIONAL — the backend `handouts` domain (Fase 4) does not exist yet,
 * so there is no schemas.py to mirror. Shapes here follow
 * docs/anahita-backend-prd.md §7.8. Re-verify against the real Pydantic
 * schemas once the backend domain ships.
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
  /** Abstract storage reference (e.g. `handouts/campaign_abc/map.png`), resolved by the StorageService. */
  storage_key: string | null;
  is_revealed: boolean;
  revealed_at: string | null;
  created_at: string;
}
