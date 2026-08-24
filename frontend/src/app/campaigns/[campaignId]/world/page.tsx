"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useFactions, useLocations, useNpcs, useWorldSearch } from "@/hooks/use-world";
import type { WorldSearchResult } from "@/types/world";

const ENTITY_TYPE_LABEL: Record<WorldSearchResult["entity_type"], string> = {
  npc: "NPC",
  location: "Local",
  faction: "Facção",
  wiki_page: "Wiki",
};

/**
 * The detail route for each search hit's entity type. Wiki pages live
 * outside `/world` (`/campaigns/{id}/wiki/{id}`), everything else is a
 * `/world/{segment}/{id}` route.
 */
function resultHref(campaignId: string, result: WorldSearchResult): string {
  if (result.entity_type === "wiki_page") {
    return `/campaigns/${campaignId}/wiki/${result.id}`;
  }
  const segment: Record<Exclude<WorldSearchResult["entity_type"], "wiki_page">, string> = {
    npc: "npcs",
    location: "locations",
    faction: "factions",
  };
  return `/campaigns/${campaignId}/world/${segment[result.entity_type]}/${result.id}`;
}

export default function WorldHubPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: npcs } = useNpcs(campaignId);
  const { data: locations } = useLocations(campaignId);
  const { data: factions } = useFactions(campaignId);

  const [query, setQuery] = useState("");
  const { data: results, isFetching } = useWorldSearch(campaignId, query);

  const sections = [
    { label: "NPCs", href: `/campaigns/${campaignId}/world/npcs`, count: npcs?.length },
    {
      label: "Locais",
      href: `/campaigns/${campaignId}/world/locations`,
      count: locations?.length,
    },
    {
      label: "Facções",
      href: `/campaigns/${campaignId}/world/factions`,
      count: factions?.length,
    },
  ];

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold">World</h1>

      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Buscar NPCs, locais e facções…"
        aria-label="Buscar no world"
        className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
      />

      {query.trim() ? (
        <div className="space-y-2">
          {isFetching ? (
            <p className="text-sm text-muted-foreground">Buscando…</p>
          ) : results && results.length > 0 ? (
            <ul className="space-y-2">
              {results.map((result) => (
                <li key={`${result.entity_type}-${result.id}`}>
                  <Link
                    href={resultHref(campaignId, result)}
                    className="block rounded-lg border border-border bg-card p-3 transition-colors hover:bg-secondary/40"
                  >
                    <span className="rounded-full border border-border px-2 py-0.5 text-xs text-muted-foreground">
                      {ENTITY_TYPE_LABEL[result.entity_type]}
                    </span>
                    <p className="mt-1 font-medium">{result.name}</p>
                    <p className="text-sm text-muted-foreground">{result.snippet}</p>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nenhum resultado.</p>
          )}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-3">
          {sections.map((section) => (
            <Link
              key={section.href}
              href={section.href}
              className="rounded-lg border border-border bg-card p-4 transition-colors hover:bg-secondary/40"
            >
              <p className="text-lg font-medium">{section.label}</p>
              <p className="text-sm text-muted-foreground">{section.count ?? 0}</p>
            </Link>
          ))}
        </div>
      )}
    </main>
  );
}
