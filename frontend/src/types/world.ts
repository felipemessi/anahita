/**
 * Mirrors backend/app/world/schemas.py (Fase 3 do backend — World-building,
 * PRD §7.7). Conferido linha a linha contra os schemas Pydantic reais.
 */

export interface Npc {
  id: string;
  campaign_id: string;
  name: string;
  race: string;
  occupation: string | null;
  description: string;
  personality: string | null;
  is_alive: boolean;
  /** SRD or campaign-homebrew Monster (catalog §7.4.8) this NPC uses as a stat block. */
  stat_block_id: string | null;
  created_at: string;
}

export interface NpcCreate {
  name: string;
  race: string;
  occupation?: string | null;
  description?: string;
  personality?: string | null;
  is_alive?: boolean;
  stat_block_id?: string | null;
}

export type LocationType =
  | "city"
  | "town"
  | "dungeon"
  | "wilderness"
  | "building"
  | "region"
  | "plane";

export interface Location {
  id: string;
  campaign_id: string;
  name: string;
  location_type: LocationType;
  description: string;
  /** Hierarchy: region → city → tavern. */
  parent_location_id: string | null;
}

export interface LocationCreate {
  name: string;
  location_type: LocationType;
  description?: string;
  parent_location_id?: string | null;
}

/** A location and its descendants, as returned by GET .../locations/tree. */
export interface LocationTreeNode {
  id: string;
  name: string;
  location_type: LocationType;
  children: LocationTreeNode[];
}

export interface Faction {
  id: string;
  campaign_id: string;
  name: string;
  description: string;
  alignment: string | null;
  influence_level: string | null;
}

export interface FactionCreate {
  name: string;
  description?: string;
  alignment?: string | null;
  influence_level?: string | null;
}

export interface NpcFaction {
  id: string;
  npc_id: string;
  faction_id: string;
  role_in_faction: string | null;
}

export interface NpcFactionCreate {
  faction_id: string;
  role_in_faction?: string | null;
}

export type NpcLocationPresenceType = "resides" | "frequents" | "controls";

export interface NpcLocation {
  id: string;
  npc_id: string;
  location_id: string;
  presence_type: NpcLocationPresenceType;
}

export interface NpcLocationCreate {
  location_id: string;
  presence_type: NpcLocationPresenceType;
}

export interface NpcSession {
  id: string;
  npc_id: string;
  session_id: string;
  appearance_note: string | null;
}

export interface NpcSessionCreate {
  session_id: string;
  appearance_note?: string | null;
}

export interface LocationSession {
  id: string;
  location_id: string;
  session_id: string;
  visit_note: string | null;
}

export interface LocationSessionCreate {
  session_id: string;
  visit_note?: string | null;
}

export type FactionRelationshipType =
  | "allied"
  | "hostile"
  | "neutral"
  | "vassal"
  | "trade_partner";

export interface FactionRelationship {
  id: string;
  faction_a_id: string;
  faction_b_id: string;
  relationship_type: FactionRelationshipType;
}

export interface FactionRelationshipCreate {
  faction_b_id: string;
  relationship_type: FactionRelationshipType;
}

/** One cross-entity search hit (GET /campaigns/{id}/world/search?q=). */
export interface WorldSearchResult {
  entity_type: "npc" | "location" | "faction";
  id: string;
  name: string;
  snippet: string;
}
