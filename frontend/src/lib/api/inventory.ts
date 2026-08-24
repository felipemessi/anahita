import { apiFetch } from "@/lib/api/client";
import { listEncounters } from "@/lib/api/combat";
import { listSessions } from "@/lib/api/sessions";
import type { Encounter } from "@/types/combat";
import type {
  LootDrop,
  LootDropClaim,
  LootDropCreate,
  PartyInventoryCreate,
  PartyInventoryEntry,
  PartyInventoryUpdate,
} from "@/types/inventory";

/** Calls the inventory endpoints exposed by backend/app/inventory/router.py. */

/** List a campaign's shared party inventory. */
export function listPartyInventory(campaignId: string): Promise<PartyInventoryEntry[]> {
  return apiFetch<PartyInventoryEntry[]>(`/campaigns/${campaignId}/inventory`);
}

/** Add a stack of an item to the party inventory. DM only. */
export function addToInventory(
  campaignId: string,
  data: PartyInventoryCreate,
): Promise<PartyInventoryEntry> {
  return apiFetch<PartyInventoryEntry>(`/campaigns/${campaignId}/inventory`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update a party inventory entry's quantity/notes. DM only. */
export function updateInventoryEntry(
  campaignId: string,
  entryId: string,
  data: PartyInventoryUpdate,
): Promise<PartyInventoryEntry> {
  return apiFetch<PartyInventoryEntry>(
    `/campaigns/${campaignId}/inventory/${entryId}`,
    { method: "PATCH", body: JSON.stringify(data) },
  );
}

/** Remove a party inventory entry entirely. DM only. */
export function removeFromInventory(campaignId: string, entryId: string): Promise<void> {
  return apiFetch<void>(`/campaigns/${campaignId}/inventory/${entryId}`, {
    method: "DELETE",
  });
}

/** Record a loot drop for an encounter (item and/or currency). DM only. */
export function createLootDrop(
  encounterId: string,
  data: LootDropCreate,
): Promise<LootDrop> {
  return apiFetch<LootDrop>(`/encounters/${encounterId}/loot`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** List an encounter's loot drops. */
export function listLootDrops(encounterId: string): Promise<LootDrop[]> {
  return apiFetch<LootDrop[]>(`/encounters/${encounterId}/loot`);
}

/** Claim a loot drop for a character. The character's own player, or the DM. */
export function claimLootDrop(
  lootDropId: string,
  data: LootDropClaim,
): Promise<LootDrop> {
  return apiFetch<LootDrop>(`/loot-drops/${lootDropId}/claim`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/**
 * A campaign's loot drops across every session/encounter it's had so far.
 *
 * There's no backend endpoint that aggregates loot at the campaign level
 * (`GET /encounters/{id}/loot` is per-encounter, PRD §7.9) — this walks
 * sessions → encounters → loot to build one feed for the inventory page.
 */
export async function listCampaignLootDrops(campaignId: string): Promise<LootDrop[]> {
  const encounters = await listCampaignEncounters(campaignId);
  const lootLists = await Promise.all(
    encounters.map((encounter) => listLootDrops(encounter.id)),
  );
  return lootLists.flat();
}

/** Every encounter across a campaign's sessions — used to pick one to drop loot into. */
export async function listCampaignEncounters(campaignId: string): Promise<Encounter[]> {
  const sessions = await listSessions(campaignId);
  const encounterLists = await Promise.all(
    sessions.map((session) => listEncounters(session.id)),
  );
  return encounterLists.flat();
}
