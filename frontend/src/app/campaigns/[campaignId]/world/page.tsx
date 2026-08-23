"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { useFactions, useLocations, useNpcs } from "@/hooks/use-world";

export default function WorldHubPage() {
  const { campaignId } = useParams<{ campaignId: string }>();
  const { data: npcs } = useNpcs(campaignId);
  const { data: locations } = useLocations(campaignId);
  const { data: factions } = useFactions(campaignId);

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
    </main>
  );
}
