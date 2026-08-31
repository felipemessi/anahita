"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { CHARACTERS_QUERY_KEY } from "@/hooks/use-character";
import {
  addToInventory,
  claimLootDrop,
  createLootDrop,
  listCampaignEncounters,
  listCampaignLootDrops,
  listPartyInventory,
  removeFromInventory,
  updateInventoryEntry,
} from "@/lib/api/inventory";
import type {
  LootDropClaim,
  LootDropCreate,
  PartyInventoryCreate,
  PartyInventoryUpdate,
} from "@/types/inventory";

export const INVENTORY_QUERY_KEY = ["inventory"] as const;
export const LOOT_QUERY_KEY = ["loot"] as const;

/** A campaign's shared party inventory. */
export function usePartyInventory(campaignId: string) {
  return useQuery({
    queryKey: [...INVENTORY_QUERY_KEY, campaignId],
    queryFn: () => listPartyInventory(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Add an item to the party inventory (DM only); invalidates the inventory list. */
export function useAddToInventory(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: PartyInventoryCreate) => addToInventory(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...INVENTORY_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Update a party inventory entry's quantity/notes (DM only). */
export function useUpdateInventoryEntry(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ entryId, data }: { entryId: string; data: PartyInventoryUpdate }) =>
      updateInventoryEntry(campaignId, entryId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...INVENTORY_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Remove a party inventory entry (DM only). */
export function useRemoveFromInventory(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) => removeFromInventory(campaignId, entryId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...INVENTORY_QUERY_KEY, campaignId],
      });
    },
  });
}

/** Every loot drop across the campaign's sessions/encounters so far. */
export function useCampaignLootDrops(campaignId: string) {
  return useQuery({
    queryKey: [...LOOT_QUERY_KEY, campaignId],
    queryFn: () => listCampaignLootDrops(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Every encounter across the campaign's sessions — to pick one to drop loot into. */
export function useCampaignEncounters(campaignId: string) {
  return useQuery({
    queryKey: [...LOOT_QUERY_KEY, campaignId, "encounters"],
    queryFn: () => listCampaignEncounters(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Record a loot drop for an encounter (DM only); invalidates the campaign's loot feed. */
export function useCreateLootDrop(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      encounterId,
      data,
    }: {
      encounterId: string;
      data: LootDropCreate;
    }) => createLootDrop(encounterId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [...LOOT_QUERY_KEY, campaignId] });
    },
  });
}

/**
 * Claim a loot drop for a character (the player's own, or — via the DM
 * "atribuir a..." menu — any character in the campaign). Invalidates the
 * campaign's loot feed and the claiming character's sheet, since the
 * backend now merges the claimed item into `CharacterEquipment` (Fase 14).
 */
export function useClaimLootDrop(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      lootDropId,
      data,
    }: {
      lootDropId: string;
      data: LootDropClaim;
    }) => claimLootDrop(lootDropId, data),
    onSuccess: (_lootDrop, variables) => {
      void queryClient.invalidateQueries({ queryKey: [...LOOT_QUERY_KEY, campaignId] });
      void queryClient.invalidateQueries({
        queryKey: [...CHARACTERS_QUERY_KEY, variables.data.character_id],
      });
    },
  });
}
