import { apiFetch } from "@/lib/api/client";
import type {
  Faction,
  FactionCreate,
  FactionRelationship,
  FactionRelationshipCreate,
  Location,
  LocationCreate,
  LocationSession,
  LocationSessionCreate,
  LocationTreeNode,
  Npc,
  NpcCreate,
  NpcFaction,
  NpcFactionCreate,
  NpcLocation,
  NpcLocationCreate,
  NpcSession,
  NpcSessionCreate,
  WorldSearchResult,
} from "@/types/world";

/** Calls the world-building endpoints exposed by backend/app/world/router.py. */

/** List a campaign's NPCs. */
export function listNpcs(campaignId: string): Promise<Npc[]> {
  return apiFetch<Npc[]>(`/campaigns/${campaignId}/npcs`);
}

/** Create an NPC for a campaign; only the campaign's DM may do this. */
export function createNpc(campaignId: string, data: NpcCreate): Promise<Npc> {
  return apiFetch<Npc>(`/campaigns/${campaignId}/npcs`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List a campaign's locations (flat, unordered by hierarchy). */
export function listLocations(campaignId: string): Promise<Location[]> {
  return apiFetch<Location[]>(`/campaigns/${campaignId}/locations`);
}

/** Create a location for a campaign; only the campaign's DM may do this. */
export function createLocation(
  campaignId: string,
  data: LocationCreate,
): Promise<Location> {
  return apiFetch<Location>(`/campaigns/${campaignId}/locations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** A campaign's locations nested by parent, root locations first. */
export function getLocationTree(campaignId: string): Promise<LocationTreeNode[]> {
  return apiFetch<LocationTreeNode[]>(`/campaigns/${campaignId}/locations/tree`);
}

/** Reparent a location; rejects any change that would create a cycle. */
export function updateLocationParent(
  locationId: string,
  parentLocationId: string | null,
): Promise<Location> {
  return apiFetch<Location>(`/locations/${locationId}/parent`, {
    method: "PATCH",
    body: JSON.stringify({ parent_location_id: parentLocationId }),
  });
}

/** List a campaign's factions. */
export function listFactions(campaignId: string): Promise<Faction[]> {
  return apiFetch<Faction[]>(`/campaigns/${campaignId}/factions`);
}

/** Create a faction for a campaign; only the campaign's DM may do this. */
export function createFaction(
  campaignId: string,
  data: FactionCreate,
): Promise<Faction> {
  return apiFetch<Faction>(`/campaigns/${campaignId}/factions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List an NPC's faction links. */
export function listNpcFactions(npcId: string): Promise<NpcFaction[]> {
  return apiFetch<NpcFaction[]>(`/npcs/${npcId}/factions`);
}

/** Link an NPC to a faction from their own campaign; DM-only. */
export function linkNpcFaction(
  npcId: string,
  data: NpcFactionCreate,
): Promise<NpcFaction> {
  return apiFetch<NpcFaction>(`/npcs/${npcId}/factions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List an NPC's location links. */
export function listNpcLocations(npcId: string): Promise<NpcLocation[]> {
  return apiFetch<NpcLocation[]>(`/npcs/${npcId}/locations`);
}

/** Link an NPC to a location from their own campaign; DM-only. */
export function linkNpcLocation(
  npcId: string,
  data: NpcLocationCreate,
): Promise<NpcLocation> {
  return apiFetch<NpcLocation>(`/npcs/${npcId}/locations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List an NPC's session appearances. */
export function listNpcSessions(npcId: string): Promise<NpcSession[]> {
  return apiFetch<NpcSession[]>(`/npcs/${npcId}/sessions`);
}

/** Link an NPC to a session appearance from their own campaign; DM-only. */
export function linkNpcSession(
  npcId: string,
  data: NpcSessionCreate,
): Promise<NpcSession> {
  return apiFetch<NpcSession>(`/npcs/${npcId}/sessions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List a location's session visits. */
export function listLocationSessions(locationId: string): Promise<LocationSession[]> {
  return apiFetch<LocationSession[]>(`/locations/${locationId}/sessions`);
}

/** Link a location to a session visit from their own campaign; DM-only. */
export function linkLocationSession(
  locationId: string,
  data: LocationSessionCreate,
): Promise<LocationSession> {
  return apiFetch<LocationSession>(`/locations/${locationId}/sessions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List a faction's relationships (as either side). */
export function listFactionRelationships(
  factionId: string,
): Promise<FactionRelationship[]> {
  return apiFetch<FactionRelationship[]>(`/factions/${factionId}/relationships`);
}

/** Set a relationship between two factions from the same campaign; DM-only. */
export function linkFactionRelationship(
  factionId: string,
  data: FactionRelationshipCreate,
): Promise<FactionRelationship> {
  return apiFetch<FactionRelationship>(`/factions/${factionId}/relationships`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Search a campaign's NPCs, locations, and factions by name/description. */
export function searchWorld(
  campaignId: string,
  query: string,
): Promise<WorldSearchResult[]> {
  return apiFetch<WorldSearchResult[]>(
    `/campaigns/${campaignId}/world/search?q=${encodeURIComponent(query)}`,
  );
}
