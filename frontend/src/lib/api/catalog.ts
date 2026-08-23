import { apiFetch } from "@/lib/api/client";
import type {
  Background,
  BackgroundSummary,
  CatalogCategory,
  ClassDefinition,
  ClassSummary,
  Feat,
  FeatSummary,
  Item,
  ItemSummary,
  MagicItem,
  MagicItemSummary,
  Monster,
  MonsterSummary,
  Race,
  RaceSummary,
  Rule,
  RuleSummary,
  Spell,
  SpellSummary,
} from "@/types/catalog";

/**
 * Read-only SRD catalog client (backend/app/catalog/router.py). There is no
 * homebrew-creation endpoint yet — see `custom-entry-form.tsx` and the
 * backlog note on "Como DM, quero criar conteúdo homebrew".
 *
 * The 9 categories with a dedicated screen (PRD §6.1a). Each maps to its
 * backend path — `equipment` is the only one that doesn't match 1:1
 * (backend calls it `items`).
 */
export const CATALOG_CATEGORY_PATH: Record<CatalogCategory, string> = {
  races: "races",
  classes: "classes",
  spells: "spells",
  equipment: "items",
  "magic-items": "magic-items",
  monsters: "monsters",
  backgrounds: "backgrounds",
  feats: "feats",
  rules: "rules",
};

export interface CatalogSummaryByCategory {
  races: RaceSummary;
  classes: ClassSummary;
  spells: SpellSummary;
  equipment: ItemSummary;
  "magic-items": MagicItemSummary;
  monsters: MonsterSummary;
  backgrounds: BackgroundSummary;
  feats: FeatSummary;
  rules: RuleSummary;
}

export interface CatalogDetailByCategory {
  races: Race;
  classes: ClassDefinition;
  spells: Spell;
  equipment: Item;
  "magic-items": MagicItem;
  monsters: Monster;
  backgrounds: Background;
  feats: Feat;
  rules: Rule;
}

export interface CatalogListFilters {
  search?: string;
  /** Category-specific filters (`level`/`school` for spells, `item_type` for equipment, …). */
  [key: string]: string | number | boolean | undefined;
}

/** List entries of a catalog category, optionally filtered and locale-aware. */
export function listCatalogEntries<C extends CatalogCategory>(
  category: C,
  { search, locale, ...filters }: CatalogListFilters & { locale?: string } = {},
): Promise<CatalogSummaryByCategory[C][]> {
  const params = new URLSearchParams();
  if (search) params.set("search", search);
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined) params.set(key, String(value));
  }
  const query = params.toString();
  const path = `/catalog/${CATALOG_CATEGORY_PATH[category]}${query ? `?${query}` : ""}`;
  return apiFetch<CatalogSummaryByCategory[C][]>(path, { locale });
}

/** Get a single catalog entry by ID, with full detail. */
export function getCatalogEntry<C extends CatalogCategory>(
  category: C,
  entryId: string,
  locale?: string,
): Promise<CatalogDetailByCategory[C]> {
  return apiFetch<CatalogDetailByCategory[C]>(
    `/catalog/${CATALOG_CATEGORY_PATH[category]}/${entryId}`,
    { locale },
  );
}

/**
 * Create a homebrew entry in a catalog category, always scoped to a
 * campaign (`is_custom=true` + `campaign_id`, never global — PRD §6.1a).
 *
 * NOTE: `backend/app/catalog/router.py` is read-only today — there is no
 * `POST /catalog/{category}` endpoint yet. This calls the REST shape the
 * backend is expected to expose once that story is picked up there; until
 * then it will fail with a 404/405, which `custom-entry-form.tsx` surfaces
 * as an error instead of pretending to succeed.
 */
export function createCustomEntry<C extends CatalogCategory>(
  category: C,
  campaignId: string,
  fields: Record<string, unknown>,
): Promise<CatalogDetailByCategory[C]> {
  return apiFetch<CatalogDetailByCategory[C]>(`/catalog/${CATALOG_CATEGORY_PATH[category]}`, {
    method: "POST",
    body: JSON.stringify({ ...fields, is_custom: true, campaign_id: campaignId }),
  });
}
