"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { CatalogFilterBar } from "@/components/catalog/catalog-filter-bar";
import { CatalogList } from "@/components/catalog/catalog-list";
import { useMyMembership } from "@/hooks/use-campaign";
import { useCatalogList } from "@/hooks/use-catalog";
import { isSupportedCatalogCategory } from "@/lib/utils/catalog-category";

export default function CatalogCategoryPage() {
  const { campaignId, category } = useParams<{
    campaignId: string;
    category: string;
  }>();
  const [search, setSearch] = useState("");

  if (!isSupportedCatalogCategory(category)) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Categoria de catálogo desconhecida.</p>
      </main>
    );
  }

  return (
    <CatalogCategoryList campaignId={campaignId} category={category} search={search} onSearchChange={setSearch} />
  );
}

function CatalogCategoryList({
  campaignId,
  category,
  search,
  onSearchChange,
}: {
  campaignId: string;
  category: Parameters<typeof useCatalogList>[0];
  search: string;
  onSearchChange: (value: string) => void;
}) {
  const { data: entries, isLoading } = useCatalogList(category, {
    search,
    campaign_id: campaignId,
  });
  const { data: membership } = useMyMembership(campaignId);

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold capitalize">{category.replace("-", " ")}</h1>
        {membership?.role === "dm" ? (
          <Link
            href={`/campaigns/${campaignId}/catalog/${category}/new`}
            className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-secondary"
          >
            Criar homebrew
          </Link>
        ) : null}
      </div>
      <CatalogFilterBar search={search} onSearchChange={onSearchChange} />
      {isLoading ? (
        <p className="text-sm text-muted-foreground">Carregando…</p>
      ) : (
        <CatalogList campaignId={campaignId} category={category} entries={entries ?? []} />
      )}
    </main>
  );
}
