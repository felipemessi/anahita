/**
 * Mirrors backend/app/wiki/schemas.py (Fase 5 do backend — Registro e Lore,
 * PRD §7.10). Reading is open to any campaign member; writing is DM-only.
 */

export interface WikiPageLink {
  id: string;
  wiki_page_id: string;
  npc_id: string | null;
  location_id: string | null;
  faction_id: string | null;
}

/** Exactly one of npc_id/location_id/faction_id must be set. */
export interface WikiPageLinkCreate {
  npc_id?: string | null;
  location_id?: string | null;
  faction_id?: string | null;
}

/** Summary shape used by the list view (GET /campaigns/{id}/wiki). */
export interface WikiPageSummary {
  id: string;
  title: string;
  slug: string;
  tags: string | null;
}

/** Full page shape used by the detail view (GET /wiki/{pageId}). */
export interface WikiPage {
  id: string;
  campaign_id: string;
  title: string;
  slug: string;
  content: string;
  tags: string | null;
  created_by_id: string | null;
  created_at: string;
  links: WikiPageLink[];
}

export interface WikiPageCreate {
  title: string;
  content?: string;
  tags?: string | null;
}

export interface WikiPageUpdate {
  title?: string;
  content?: string;
  tags?: string | null;
}
