"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { CATALOG_QUERY_KEY_PREFIX } from "@/components/catalog/locale-switcher";
import {
  createCustomEntry,
  getCatalogEntry,
  getFeature,
  listCatalogEntries,
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
