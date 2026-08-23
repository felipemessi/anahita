"use client";

import { useParams, useRouter } from "next/navigation";

import { CustomEntryForm } from "@/components/catalog/custom-entry-form";
import { useMyMembership } from "@/hooks/use-campaign";
import { isSupportedCatalogCategory } from "@/lib/utils/catalog-category";

/** Homebrew creation screen — DM only, always scoped to the current campaign. */
export default function NewCatalogEntryPage() {
  const { campaignId, category } = useParams<{ campaignId: string; category: string }>();
  const router = useRouter();
  const { data: membership } = useMyMembership(campaignId);

  if (!isSupportedCatalogCategory(category)) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Categoria de catálogo desconhecida.</p>
      </main>
    );
  }

  if (membership && membership.role !== "dm") {
    return (
      <main className="mx-auto max-w-2xl px-6 py-10">
        <p className="text-sm text-muted-foreground">
          Apenas o mestre pode criar conteúdo homebrew.
        </p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-bold capitalize">
        Novo homebrew — {category.replace("-", " ")}
      </h1>
      <CustomEntryForm
        category={category}
        campaignId={campaignId}
        onCreated={(entry) =>
          router.push(`/campaigns/${campaignId}/catalog/${category}/${entry.id}`)
        }
      />
    </main>
  );
}
