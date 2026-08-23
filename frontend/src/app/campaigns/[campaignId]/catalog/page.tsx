"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import type { CatalogCategory } from "@/types/catalog";

const CATEGORIES: Array<{ slug: CatalogCategory; label: string }> = [
  { slug: "races", label: "Raças" },
  { slug: "classes", label: "Classes" },
  { slug: "spells", label: "Magias" },
  { slug: "equipment", label: "Equipamento" },
  { slug: "magic-items", label: "Itens Mágicos" },
  { slug: "monsters", label: "Monstros" },
  { slug: "backgrounds", label: "Antecedentes" },
  { slug: "feats", label: "Talentos" },
  { slug: "rules", label: "Regras" },
];

/** Hub with a tab per catalog category (SRD + campaign homebrew — PRD §6.1a). */
export default function CatalogHubPage() {
  const { campaignId } = useParams<{ campaignId: string }>();

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <div>
        <h1 className="text-2xl font-bold">Catálogo</h1>
        <p className="text-sm text-muted-foreground">
          SRD 2014 e conteúdo homebrew desta campanha.
        </p>
      </div>

      <nav
        aria-label="Categorias do catálogo"
        className="grid grid-cols-2 gap-2 sm:grid-cols-3"
      >
        {CATEGORIES.map((category) => (
          <Link
            key={category.slug}
            href={`/campaigns/${campaignId}/catalog/${category.slug}`}
            className="rounded-lg border border-border bg-card px-4 py-3 text-center text-sm font-medium transition-colors hover:bg-secondary/40"
          >
            {category.label}
          </Link>
        ))}
      </nav>
    </main>
  );
}
