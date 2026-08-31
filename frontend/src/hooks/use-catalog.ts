"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { CATALOG_QUERY_KEY_PREFIX } from "@/components/catalog/locale-switcher";
import {
  addRaceAbilityBonus,
  addRaceSubrace,
  addRaceTrait,
  createCustomEntry,
  deleteCustomEntry,
  getAbilityScores,
  getCatalogEntry,
  getFeature,
  listCatalogEntries,
  listLanguages,
  listProficiencies,
  type CatalogListFilters,
} from "@/lib/api/catalog";
import { getClientLocale } from "@/lib/i18n/locale";
import type { CatalogCategory } from "@/types/catalog";

/**
 * List a catalog category, locale-aware. Query keys share
 * `CATALOG_QUERY_KEY_PREFIX` with `locale-switcher.tsx` so switching locale
 * invalidates every catalog query in one call (see PRD §3.4).
 */
export function useCatalogList<C extends CatalogCategory>(
  category: C,
  filters: CatalogListFilters = {},
) {
  const locale = getClientLocale();
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, category, "list", locale, filters],
    queryFn: () => listCatalogEntries(category, { ...filters, locale }),
  });
}

/** Get a single catalog entry's full detail, locale-aware. */
export function useCatalogEntry<C extends CatalogCategory>(
  category: C,
  entryId: string,
) {
  const locale = getClientLocale();
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, category, "detail", entryId, locale],
    queryFn: () => getCatalogEntry(category, entryId, locale),
    enabled: Boolean(entryId),
  });
}

/** Get a single catalog feature by ID (e.g. to resolve a picked level-up option's name). */
export function useCatalogFeature(featureId: string) {
  const locale = getClientLocale();
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, "features", "detail", featureId, locale],
    queryFn: () => getFeature(featureId, locale),
    enabled: Boolean(featureId),
  });
}

/**
 * The 6 core ability scores — small, fixed, and locale-independent
 * (`index` only), so this is fetched and cached once for the whole app.
 */
export function useAbilityScores() {
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, "ability-scores", "list"],
    queryFn: getAbilityScores,
    staleTime: Infinity,
  });
}

/**
 * All languages (SRD + homebrew) — the pickable set for a homebrew race's
 * `language_ids` field (Fase 11). Small and locale-independent, so cached
 * once for the whole app like `useAbilityScores`.
 */
export function useLanguages() {
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, "languages", "list"],
    queryFn: listLanguages,
    staleTime: Infinity,
  });
}

/**
 * All proficiencies (SRD + homebrew) — the pickable set for a homebrew
 * race's `proficiency_ids` field (Fase 11).
 */
export function useProficiencies() {
  return useQuery({
    queryKey: [...CATALOG_QUERY_KEY_PREFIX, "proficiencies", "list"],
    queryFn: listProficiencies,
    staleTime: Infinity,
  });
}

/** Create a homebrew entry for `category`, always scoped to `campaignId`. */
export function useCreateCustomEntry<C extends CatalogCategory>(
  category: C,
  campaignId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (fields: Record<string, unknown>) =>
      createCustomEntry(category, campaignId, fields),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CATALOG_QUERY_KEY_PREFIX, category],
      });
    },
  });
}

/**
 * Delete a homebrew entry for `category` — DM only, own campaign (Fase 11).
 * Invalidates every cached query for the category so both the list and any
 * cached detail view drop the deleted entry.
 */
export function useDeleteCustomEntry<C extends CatalogCategory>(category: C) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (entryId: string) => deleteCustomEntry(category, entryId),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CATALOG_QUERY_KEY_PREFIX, category],
      });
    },
  });
}

/**
 * Attach an ability bonus/trait/subrace to a just-created homebrew race
 * (Fase 11) — invalidates the race's own detail query so the "read back"
 * view reflects the newly attached content.
 */
export function useAddRaceAbilityBonus(raceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { ability: string; bonus: number }) =>
      addRaceAbilityBonus(raceId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CATALOG_QUERY_KEY_PREFIX, "races", "detail", raceId],
      });
    },
  });
}

export function useAddRaceTrait(raceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      trait_name: string;
      description: string;
      mechanical_effect: string | null;
    }) => addRaceTrait(raceId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CATALOG_QUERY_KEY_PREFIX, "races", "detail", raceId],
      });
    },
  });
}

export function useAddRaceSubrace(raceId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: {
      name: string;
      description: string;
      ability_bonuses: { ability: string; bonus: number }[];
      traits: { trait_name: string; description: string; mechanical_effect: string | null }[];
    }) => addRaceSubrace(raceId, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: [...CATALOG_QUERY_KEY_PREFIX, "races", "detail", raceId],
      });
    },
  });
}
