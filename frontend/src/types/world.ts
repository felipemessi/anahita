/**
 * PROVISIONAL — the backend `world` domain (Fase 3) does not exist yet, so
 * there is no schemas.py to mirror. Shapes here follow
 * docs/anahita-backend-prd.md §7.7. Re-verify against the real Pydantic
 * schemas once the backend domain ships.
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

export interface Faction {
  id: string;
  campaign_id: string;
  name: string;
  description: string;
  alignment: string | null;
  influence_level: string | null;
}

export interface NpcFaction {
  npc_id: string;
  faction_id: string;
  role_in_faction: string | null;
}

export type NpcLocationPresenceType = "resides" | "frequents" | "controls";

export interface NpcLocation {
  npc_id: string;
  location_id: string;
  presence_type: NpcLocationPresenceType;
}

export interface NpcSession {
  npc_id: string;
  session_id: string;
  appearance_note: string | null;
}

export interface LocationSession {
  location_id: string;
  session_id: string;
  visit_note: string | null;
}

export type FactionRelationshipType =
  | "allied"
  | "hostile"
  | "neutral"
  | "vassal"
  | "trade_partner";

export interface FactionRelationship {
  faction_a_id: string;
  faction_b_id: string;
  relationship_type: FactionRelationshipType;
}
