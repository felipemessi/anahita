import type { CatalogCategory } from "@/types/catalog";

/** The 9 catalog categories with a dedicated screen (PRD §6.1a). */
export const CATALOG_CATEGORIES: readonly CatalogCategory[] = [
  "races",
  "classes",
  "spells",
  "equipment",
  "magic-items",
  "monsters",
  "backgrounds",
  "feats",
  "rules",
];

/** Narrow an arbitrary route param to a known `CatalogCategory`. */
export function isSupportedCatalogCategory(
  value: string | undefined | null,
): value is CatalogCategory {
  return (CATALOG_CATEGORIES as readonly string[]).includes(value ?? "");
}
