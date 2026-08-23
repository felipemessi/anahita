"use client";

import { useParams } from "next/navigation";

import { useFactionRelationships, useFactions } from "@/hooks/use-world";
import type { FactionRelationshipType } from "@/types/world";

const RELATIONSHIP_LABEL: Record<FactionRelationshipType, string> = {
  allied: "aliada de",
  hostile: "hostil a",
  neutral: "neutra com",
  vassal: "vassala de",
  trade_partner: "parceira comercial de",
};

export default function FactionDetailPage() {
  const { campaignId, factionId } = useParams<{
    campaignId: string;
    factionId: string;
  }>();
  const { data: factions, isLoading } = useFactions(campaignId);
  const faction = factions?.find((candidate) => candidate.id === factionId);
  const factionsById = new Map((factions ?? []).map((f) => [f.id, f]));

  const { data: relationships } = useFactionRelationships(factionId);

  if (isLoading) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Carregando…</p>
      </main>
    );
  }
  if (!faction) {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-sm text-muted-foreground">Facção não encontrada.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <header>
        <h1 className="text-2xl font-bold">{faction.name}</h1>
        {faction.alignment || faction.influence_level ? (
          <p className="text-sm text-muted-foreground">
            {[faction.alignment, faction.influence_level].filter(Boolean).join(" · ")}
          </p>
        ) : null}
      </header>

      {faction.description ? <p className="text-sm">{faction.description}</p> : null}

      <section className="space-y-1">
        <h2 className="text-sm font-medium text-muted-foreground">Relações</h2>
        {relationships && relationships.length > 0 ? (
          <ul className="text-sm">
            {relationships.map((relationship) => {
              const otherId =
                relationship.faction_a_id === faction.id
                  ? relationship.faction_b_id
                  : relationship.faction_a_id;
              const other = factionsById.get(otherId);
              return (
                <li key={relationship.id}>
                  {RELATIONSHIP_LABEL[relationship.relationship_type]}{" "}
                  {other?.name ?? otherId}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Nenhuma.</p>
        )}
      </section>
    </main>
  );
}
