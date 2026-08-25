"use client";

import { useCombat } from "@/hooks/use-combat";

/**
 * Blocks turn advancement until every active participant has rolled
 * initiative — shown once the encounter is active and any participant is
 * still missing one. Any campaign member may roll for their own
 * participant; the DM may roll for any (server-enforced, see
 * `useCombat().rollInitiative`).
 */
export function InitiativePrompt() {
  const { encounter, rollInitiative } = useCombat();

  if (!encounter || encounter.status !== "active") return null;
  const missing = encounter.participants.filter(
    (p) => p.is_active && p.initiative === null,
  );
  if (missing.length === 0) return null;

  return (
    <section
      aria-label="Rolagem de iniciativa"
      className="rounded-lg border border-border bg-card p-4"
    >
      <h2 className="font-semibold">Rolagem de iniciativa</h2>
      <p className="mt-1 text-sm text-muted-foreground">
        O combate só avança quando todos os participantes rolarem iniciativa.
      </p>
      <ul className="mt-2 space-y-1">
        {missing.map((participant) => (
          <li key={participant.id} className="flex items-center justify-between text-sm">
            <span>{participant.name}</span>
            <button
              type="button"
              onClick={() => rollInitiative(participant.id)}
              className="rounded-md border border-border px-3 py-1 text-xs hover:bg-secondary"
            >
              Rolar iniciativa
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
