"use client";

import Link from "next/link";

import type { CatalogCategory } from "@/types/catalog";

/** Common shape shared by every catalog summary type. */
export interface CatalogListEntry {
  id: string;
  name: string;
  is_custom: boolean;
}

export function CatalogList({
  campaignId,
  category,
  entries,
}: {
  campaignId: string;
  category: CatalogCategory;
  entries: CatalogListEntry[];
}) {
  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Nenhum resultado encontrado.</p>
    );
  }

  return (
    <ul className="space-y-2">
      {entries.map((entry) => (
        <li key={entry.id}>
          <Link
            href={`/campaigns/${campaignId}/catalog/${category}/${entry.id}`}
            className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3 transition-colors hover:bg-secondary/40"
          >
            <span>{entry.name}</span>
            <span
              className={`rounded-full px-2 py-0.5 text-xs ${
                entry.is_custom
                  ? "bg-secondary text-secondary-foreground"
                  : "border border-border text-muted-foreground"
              }`}
            >
              {entry.is_custom ? "Homebrew" : "SRD"}
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
