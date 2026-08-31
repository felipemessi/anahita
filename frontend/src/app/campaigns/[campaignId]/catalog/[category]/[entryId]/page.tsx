"use client";

import { useParams } from "next/navigation";

import { CatalogEntryDetail } from "@/components/catalog/catalog-entry-detail";
import { useCatalogEntry } from "@/hooks/use-catalog";
import { isSupportedCatalogCategory } from "@/lib/utils/catalog-category";

export default function CatalogEntryPage() {
  const { campaignId, category, entryId } = useParams<{
    campaignId: string;
    category: string;
    entryId: string;
  }>();

  if (!isSupportedCatalogCategory(category)) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Categoria de catálogo desconhecida.</p>
      </main>
    );
  }

  return <CatalogEntryContent campaignId={campaignId} category={category} entryId={entryId} />;
}

function CatalogEntryContent({
  campaignId,
  category,
  entryId,
}: {
  campaignId: string;
  category: Parameters<typeof useCatalogEntry>[0];
  entryId: string;
}) {
  const { data: entry, isLoading } = useCatalogEntry(category, entryId);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </main>
    );
  }

  if (!entry) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Entrada não encontrada.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <CatalogEntryDetail category={category} entry={entry} campaignId={campaignId} />
    </main>
  );
}
