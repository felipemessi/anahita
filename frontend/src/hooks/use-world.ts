"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  createFaction,
  createLocation,
  createNpc,
  getLocationTree,
  linkFactionRelationship,
  linkLocationSession,
  linkNpcFaction,
  linkNpcLocation,
  linkNpcSession,
  listFactionRelationships,
  listFactions,
  listLocations,
  listLocationSessions,
  listNpcFactions,
  listNpcLocations,
  listNpcs,
  listNpcSessions,
  revealNpc,
  searchWorld,
  updateLocationParent,
} from "@/lib/api/world";
import type {
  FactionCreate,
  FactionRelationshipCreate,
  LocationCreate,
  LocationSessionCreate,
  NpcCreate,
  NpcFactionCreate,
  NpcLocationCreate,
  NpcSessionCreate,
} from "@/types/world";

export const WORLD_QUERY_KEY = ["world"] as const;

/** A campaign's NPCs. */
export function useNpcs(campaignId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, campaignId, "npcs"],
    queryFn: () => listNpcs(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create an NPC (DM only); invalidates the campaign's NPC list on success. */
export function useCreateNpc(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NpcCreate) => createNpc(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, campaignId, "npcs"],
      });
    },
  });
}

/** Reveal an NPC to players (DM only); invalidates the campaign's NPC list. */
export function useRevealNpc(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (npcId: string) => revealNpc(npcId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, campaignId, "npcs"],
      });
    },
  });
}

/** A campaign's locations, flat (unordered by hierarchy). */
export function useLocations(campaignId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, campaignId, "locations"],
    queryFn: () => listLocations(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** A campaign's locations nested by parent, root locations first. */
export function useLocationTree(campaignId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, campaignId, "locations", "tree"],
    queryFn: () => getLocationTree(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a location (DM only); invalidates the campaign's location list/tree. */
export function useCreateLocation(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LocationCreate) => createLocation(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, campaignId, "locations"],
      });
    },
  });
}

/** Reparent a location (DM only); invalidates the campaign's location list/tree. */
export function useUpdateLocationParent(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      locationId,
      parentLocationId,
    }: {
      locationId: string;
      parentLocationId: string | null;
    }) => updateLocationParent(locationId, parentLocationId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, campaignId, "locations"],
      });
    },
  });
}

/** A campaign's factions. */
export function useFactions(campaignId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, campaignId, "factions"],
    queryFn: () => listFactions(campaignId),
    enabled: Boolean(campaignId),
  });
}

/** Create a faction (DM only); invalidates the campaign's faction list on success. */
export function useCreateFaction(campaignId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FactionCreate) => createFaction(campaignId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, campaignId, "factions"],
      });
    },
  });
}

/** An NPC's faction links. */
export function useNpcFactions(npcId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "factions"],
    queryFn: () => listNpcFactions(npcId),
    enabled: Boolean(npcId),
  });
}

/** Link an NPC to a faction (DM only); invalidates that NPC's faction links. */
export function useLinkNpcFaction(npcId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NpcFactionCreate) => linkNpcFaction(npcId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "factions"],
      });
    },
  });
}

/** An NPC's location links. */
export function useNpcLocations(npcId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "locations"],
    queryFn: () => listNpcLocations(npcId),
    enabled: Boolean(npcId),
  });
}

/** Link an NPC to a location (DM only); invalidates that NPC's location links. */
export function useLinkNpcLocation(npcId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NpcLocationCreate) => linkNpcLocation(npcId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "locations"],
      });
    },
  });
}

/** An NPC's session appearances. */
export function useNpcSessions(npcId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "sessions"],
    queryFn: () => listNpcSessions(npcId),
    enabled: Boolean(npcId),
  });
}

/** Link an NPC to a session appearance (DM only); invalidates that NPC's sessions. */
export function useLinkNpcSession(npcId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NpcSessionCreate) => linkNpcSession(npcId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, "npcs", npcId, "sessions"],
      });
    },
  });
}

/** A location's session visits. */
export function useLocationSessions(locationId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, "locations", locationId, "sessions"],
    queryFn: () => listLocationSessions(locationId),
    enabled: Boolean(locationId),
  });
}

/** Link a location to a session visit (DM only); invalidates that location's sessions. */
export function useLinkLocationSession(locationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: LocationSessionCreate) => linkLocationSession(locationId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, "locations", locationId, "sessions"],
      });
    },
  });
}

/** A faction's relationships (as either side). */
export function useFactionRelationships(factionId: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, "factions", factionId, "relationships"],
    queryFn: () => listFactionRelationships(factionId),
    enabled: Boolean(factionId),
  });
}

/** Set a relationship between two factions (DM only); invalidates both sides. */
export function useLinkFactionRelationship(factionId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FactionRelationshipCreate) =>
      linkFactionRelationship(factionId, data),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({
        queryKey: [...WORLD_QUERY_KEY, "factions", factionId, "relationships"],
      });
      void queryClient.invalidateQueries({
        queryKey: [
          ...WORLD_QUERY_KEY,
          "factions",
          variables.faction_b_id,
          "relationships",
        ],
      });
    },
  });
}

/** Cross-entity search over a campaign's NPCs, locations, and factions. */
export function useWorldSearch(campaignId: string, query: string) {
  return useQuery({
    queryKey: [...WORLD_QUERY_KEY, campaignId, "search", query],
    queryFn: () => searchWorld(campaignId, query),
    enabled: Boolean(campaignId) && query.trim().length > 0,
  });
}
