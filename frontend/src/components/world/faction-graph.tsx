"use client";

import { useFactionRelationships } from "@/hooks/use-world";
import type { Faction, FactionRelationshipType } from "@/types/world";

const RELATIONSHIP_LABEL: Record<FactionRelationshipType, string> = {
  allied: "aliada de",
  hostile: "hostil a",
  neutral: "neutra com",
  vassal: "vassala de",
  trade_partner: "parceira comercial de",
};

function FactionRelationships({
  faction,
  factionsById,
}: {
  faction: Faction;
  factionsById: Map<string, Faction>;
}) {
  const { data: relationships } = useFactionRelationships(faction.id);
  if (!relationships || relationships.length === 0) return null;

  return (
    <ul className="ml-4 mt-1 space-y-1 border-l border-border pl-3 text-sm text-muted-foreground">
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
  );
}

/** Per-faction relationship list (PRD calls for "lista de relações ou grafo simples"). */
export function FactionGraph({ factions }: { factions: Faction[] }) {
  if (factions.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Nenhuma facção nesta campanha ainda.
      </p>
    );
  }

  const factionsById = new Map(factions.map((faction) => [faction.id, faction]));

  return (
    <ul className="space-y-3">
      {factions.map((faction) => (
        <li key={faction.id} className="rounded-lg border border-border bg-card p-3">
          <p className="font-medium">{faction.name}</p>
          {faction.description ? (
            <p className="text-sm text-muted-foreground">{faction.description}</p>
          ) : null}
          <FactionRelationships faction={faction} factionsById={factionsById} />
        </li>
      ))}
    </ul>
  );
}
